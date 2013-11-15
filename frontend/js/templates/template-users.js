var Users = Backbone.Model.extend({
  defaults: {
    name: "",
    email: "",
    password: "",
    contacts: "",
    permissions: ""
  }
});

var UsersCollection = Backbone.Collection.extend({
  model: Users,
  url: "/users"
});

var MainView = Backbone.View.extend({
  el: "#app",
  template: _.template( $("#mainTemplate").html() ),
  initialize: function() {
    _.bindAll(this, "render", "users");
  },
  render: function(response) {
    var self = this;
    $(this.el).html( this.template({ users: response }) );
    $("#usersGrid tr[data-id]").each(function(){
      var id = $(this).attr("data-id");
      var name = $(this).attr("data-name");
      $(this).find("a.first").click(function() {
        self.editUser(id);
      });
      $(this).find("a.last").click(function() {
        self.deleteUser(id, name);
      });
    });
  },
  users: function() {
    var self = this;
    $(".loading-message").show();
    var collection = new UsersCollection();
    collection.fetch({
      success: function(datas) {
        $(".loading-message").fadeOut("fast");
        self.render(datas.toJSON());
      },
      error: function(datas) {
        $(".loading-message").fadeOut("fast");
        $(".failed-message").fadeIn("fast");
      }
    });
  },
  editUser: function(id) {
    var route = new Router();
    route.navigate("user/edit/" + id, {trigger: true});
  },
  deleteUser: function(id, name) {
    if (confirm("Are you sure to delete?")) {
      var collection = new UsersCollection();
      collection.fetch({
        data: { id_delete: id },
        success: function(data) {
          $('#usersGrid tr[data-id="' + id + '"]').fadeOut('fast');
          $(".error-message").hide();
          $(".success-message").fadeIn("fast");
          $("#title").text('"' + name + '" has been successfully deleted.');
        },
        error: function() {
          $(".success-message").hide();
          $(".error-message").fadeIn("fast");
          $("#title").text('Unable to delete "' + name + '". Try again.');
        }
      });
    }
  }
});

var AddUser = Backbone.View.extend({
  el: "#app",
  template: _.template( $("#addUserTemplate").html() ),
  events: {
    'submit form#frmAddUser': 'addUser'
  }, 
  render: function() {
    $(this.el).html( this.template );
  },
  addUser: function(event) {
    var fname = $("#fname").val();
    var email = $("#email").val();
    var pwd = $("#password").val();
    var contacts = $("#contacts").val();
    var permissions = $("#permissions").val();

    $.ajax({
      type: "post",
      url: "/users",
      data: {
        "name" : _.escape(fname),
        "email" : _.escape(email),
        "password" : _.escape(pwd),
        "contacts" : _.escape(contacts),
        "permissions" : _.escape(permissions)
      },
      success: function(datas) {
        window.location.hash = "#users";
      }
    });
    return false;
  }
});

var EditUser = Backbone.View.extend({
  el: "#app",
  template: _.template( $("#editUserTemplate").html() ),
  initialize: function() {
    _.bindAll(this, "render", "data");
  },
  events: {
    'submit form#frmEditUser' : 'editUser'
  },
  render: function(response) {
    $(this.el).html( this.template({ user: response }) );
  },
  data: function(id) {
    var self = this;
    $(".loading-message").show();
    var collection = new UsersCollection();
    collection.fetch({
      data: { id_edit: id },
      success: function(data) {
      $(".loading-message").fadeOut("fast");
        self.render(data.toJSON());
      },
      error: function(datas) {
        $(".loading-message").fadeOut("fast");
        $(".failed-message").fadeIn("fast");
      }
    });
  },
  editUser: function() {
    $.ajax({
      type: "post",
      url: "/users",
      data: {
        "id" : _.escape($("#id").val()),
        "name" : _.escape($("#fname").val()),
        "email" : _.escape($("#email").val()),
        "contacts" : _.escape($("#contacts").val()),
        "permissions" : _.escape($("#permissions").val())
      },
      success: function(datas) {
        window.location.hash = "#users";
      }
    });
    return false;
  }
});