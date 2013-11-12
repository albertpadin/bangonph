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
        self.editContact(id);
      });
      $(this).find("a.last").click(function() {
        self.deleteContact(id, name);
      });
    });
  },
  users: function() {
    var self = this;
    var collection = new UsersCollection();
    collection.fetch({
      success: function(datas) {
        self.render(datas.toJSON());
      }
    });
  },
  editContact: function(id) {
    var route = new Router();
    route.navigate("user/edit/" + id, {trigger: true});
  },
  deleteContact: function(id, name) {
    if (confirm("Are you sure to delete?")) {
      var collection = new UsersCollection();
      collection.fetch({
        data: { id_delete: id },
        success: function(data) {
          console.log(data.toJSON());
          $('#usersGrid tr[data-id="' + id + '"]').fadeOut('fast');
          $(".success-message").fadeIn("fast");
          $("#title").text('"' + name + '" has been successfully deleted.');
        },
        error: function() {
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
    'submit form#frmAdd': 'addUser'
  }, 
  render: function() {
    $(this.el).html( this.template );
  },
  addUser: function(event) {
    var fname = $("#fname").val();
    var email = $("#email").val();
    var pwd = $("#password").val();
    var contacts = $("#contacts").val();

    var details = {
      name: _.escape(fname),
      email: _.escape(email),
      password: _.escape(pwd),
      contacts: _.escape(contacts)
    };

    var collection = new UsersCollection();
    collection.create(details, {
      success: function(data) {
        window.location.hash = "#users";
        console.log(data.toJSON());
        $("#fname").val("");
        $("#email").val("");
        $("#password").val("");
        $("#contacts").val("");
        $(".success-message").fadeIn("fast");

        setTimeout(function() {
          $(".success-message").fadeOut("fast");
        }, 2000);
      },
      error: function(data) {
        console.log(data.toJSON());
        $(".error-message").fadeIn("fast");
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
    'submit form#frmEdit' : 'editUser'
  },
  render: function(response) {
    $(this.el).html( this.template({ user: response }) );
  },
  data: function(id) {
    var self = this;
    var collection = new UsersCollection();
    collection.fetch({
      data: { id_edit: id },
      success: function(data) {
        self.render(data.toJSON());
      }
    });
  },
  editUser: function() {
    var id = $("#id").val();
    var fname = $("#fname").val();
    var email = $("#email").val();
    var contacts = $("#contacts").val();

    var details = {
      id: id,
      name: _.escape(fname),
      email: _.escape(email),
      contacts: _.escape(contacts)
    };

    var collection = new UsersCollection();
    collection.create(details, {
      success: function(data) {
        window.location.hash = "#users";
        console.log(data.toJSON());
        $(".success-message").fadeIn("fast");

        setTimeout(function() {
          $(".success-message").fadeOut("fast");
        }, 2000);
      },
      error: function(data) {
        console.log(data.toJSON());
        $(".error-message").fadeIn("fast");
      }
    });
    return false;
  }
});

var Contacts = Backbone.Model.extend({
  defaults: {
    name: "",
    contacts: "",
    email: "",
    facebook: "",
    twitter: ""
  }
});

var ContactsCollection = Backbone.Collection.extend({
  model: Contacts,
  url: "/contacts"
});

var ContactView = Backbone.View.extend({
  el: "#app",
  template: _.template( $("#contactTemplate").html() ),
  initialize: function() {
    _.bindAll(this, "render", "contacts");
  },
  render: function(response) {
    var self = this;
    $(this.el).html( this.template({ contacts: response }) );
  },
  contacts: function() {
    var self = this;
    var contactsCollection = new ContactsCollection();
    contactsCollection.fetch({
      success: function(datas) {
        self.render(datas.toJSON());
      }
    });
  }
});

var AddContact = Backbone.View.extend({
  el: "#app",
  template: _.template( $("#addContactTemplate").html() ),
  events: {
    'submit form#frmAdd': 'add'
  }, 
  render: function() {
    $(this.el).html( this.template );
  },
  add: function() {
    var fname = $("#fname").val();
    var contacts = $("#contacts").val();
    var email = $("#email").val();
    var facebook = $("#facebook").val();
    var twitter = $("#twitter").val();

    var details = {
      name: _.escape(fname),
      contacts: _.escape(contacts),
      email: _.escape(email),
      facebook: _.escape(facebook),
      twitter: _.escape(twitter)
    };

    var contactsCollection = new ContactsCollection();
    contactsCollection.create(details, {
      success: function(data) {
        window.location.hash = "#contacts";
        console.log(data.toJSON());
      },
      error: function(data) {
        console.log(data.toJSON());
      }
    });
    return false;
  }
});

var Router = Backbone.Router.extend({
    routes: {
        "" : "renderMainPage",
        "users" : "renderUserPage",
        "user/new" : "renderAddUserPage",
        "user/edit/:id" : "renderEditUserPage",

        "contacts" : "renderContactPage",
        "contact/new" : "renderAddContactPage",

        "*default" : "defaultpage"
    },

    defaultpage: function(d) {
      var html = "<div style=\"margin-top: 15px;\" class=\"alert alert-dismissable alert-warning\"><button type=\"button\" class=\"close\" data-dismiss=\"alert\">&times;</button><strong>Error!</strong> Unhandled route<p>No access granted for: <strong>"+ d +"</strong></p></div>";
      $("#app").html(html);
    },

    // user page
    renderMainPage: function() {
      mainview.render();
      mainview.users();
    },
    renderUserPage: function() {
      mainview.render();
      mainview.users();
    },
    renderAddUserPage: function() {
      addUser.render();
    },
    renderEditUserPage: function(id) {
      editUser.render();
      editUser.data(id);
    },
    // contact page
    renderContactPage: function() {
      contactView.render();
    },
    renderAddContactPage: function() {
      addContact.render();
    }
    
});

var mainview = new MainView();
var addUser = new AddUser();
var editUser = new EditUser();

var contactView = new ContactView();
var addContact = new AddContact();

var router = new Router();
Backbone.history.start();