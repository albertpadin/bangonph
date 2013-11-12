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

// var Locations = Backbone.Model.extend({
//   defaults: {
//     name: "",
//     latlong: "",
//     featured_photo: "",
//     death_count: "",
//     affected_count: "",
//     status_board: "",
//     needs: "",
//     centers: "",
//     status: ""
//   },
//   urlRoot: "/locations"
// });

// var LocationView = Backbone.View.extend({
//   el: "#app",
//   template: _.template( $("#locationTemplate").html() ),
//   initialize: function() {
//     _.bindAll(this, "render", "locations");
//   },
//   render: function(response) {
//     var self = this;
//     $(this.el).html( this.template({ locations: response }) );
//   },
//   locations: function() {
//   }
// });

// var AddLocation = Backbone.View.extend({
//   el: "#app",
//   template: _.template( $("#addLocationTemplate").html() ),
//   events: {
//     'submit form#frmAdd': 'add'
//   }, 
//   render: function() {
//     $(this.el).html( this.template );
//   },
//   add: function() {
//     var details = {
//       name: _.escape($("#fname").val()),
//       latlong: _.escape($("#latlong").val()),
//       featured_photo: _.escape($("#featured_photo").val()),
//       death_count: _.escape($("#death_count").val()),
//       affected_count: _.escape($("#affected_count").val()),
//       status_board: _.escape($("#status_board").val()),
//       needs: _.escape($("#needs").val()),
//       centers: _.escape($("#centers").val()),
//       status: _.escape($("#status").val())
//     };
//     var locations = new Locations();
//     locations.save(details, {
//       success: function(data) {
//         window.location.hash = "#locations";
//         console.log(data.toJSON());
//       },
//       error: function(data) {
//         console.log(data.toJSON());
//       }
//     });
//     return false;
//   }
// });

var Router = Backbone.Router.extend({
    routes: {
        "" : "renderMainPage",
        "users" : "renderUserPage",
        "user/new" : "renderAddUserPage",
        "user/edit/:id" : "renderEditUserPage",

        "contacts" : "renderContactPage",
        "contact/new" : "renderAddContactPage",

        "locations" : "renderLocationPage",
        "location/new" : "renderAddLocationPage",

        "*default" : "defaultpage"
    },

    defaultpage: function(d) {
      var html = "<div style=\"margin-top: 15px;\" class=\"alert alert-dismissable alert-warning\"><button type=\"button\" class=\"close\" data-dismiss=\"alert\">&times;</button><strong>Error!</strong> Unhandled route<p>No access granted for: <strong>"+ d +"</strong></p></div>";
      $("#app").html(html);
    },
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
    renderContactPage: function() {
      contactView.render();
    },
    renderAddContactPage: function() {
      addContact.render();
    },

    // renderLocationPage: function() {
    //   locationView.render();
    // },
    // renderAddLocationPage: function() {
    //   addLocation.render();
    // }
    
});

var mainview = new MainView();
var addUser = new AddUser();
var editUser = new EditUser();

// var contactView = new ContactView();
// var addContact = new AddContact();

// var locationView = new LocationView();
// var addLocation = new AddLocation();

var router = new Router();
Backbone.history.start();