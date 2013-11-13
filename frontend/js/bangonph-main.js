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
    var collection = new UsersCollection();
    collection.fetch({
      success: function(datas) {
        self.render(datas.toJSON());
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
    $("#contactsGrid tr[data-id]").each(function(){
      var id = $(this).attr("data-id");
      $(this).find("a.first").click(function() {
        self.editContact(id);
      });
      $(this).find("a.last").click(function() {
        self.deleteContact(id);
      });
    });
  },
  contacts: function() {
    var self = this;
    var contactsCollection = new ContactsCollection();
    contactsCollection.fetch({
      success: function(datas) {
        self.render(datas.toJSON());
      }
    });
  },
  editContact: function(id) {
    var route = new Router();
    route.navigate("contact/edit/" + id, {trigger: true});
  },
  deleteContact: function(id) {
    if (confirm("Are you sure to delete?")) {
      var collection = new ContactsCollection();
      collection.fetch({
        data: { id_delete: id },
        success: function(data) {
          $('#contactsGrid tr[data-id="' + id + '"]').fadeOut('fast');
          $(".error-message").hide();
          $(".success-message").fadeIn("fast");
          $("#title").text('Successfully deleted.');
        },
        error: function() {
          $(".success-message").hide();
          $(".error-message").fadeIn("fast");
          $("#title").text('Unable to delete. Try again.');
        }
      });
    }
  }
});

var AddContact = Backbone.View.extend({
  el: "#app",
  template: _.template( $("#addContactTemplate").html() ),
  events: {
    'submit form#frmAddContact': 'addContact'
  }, 
  render: function() {
    $(this.el).html( this.template );
  },
  addContact: function() {
    $.ajax({
      type: "post",
      url: "/contacts",
      data: {
        "name" : _.escape($("#fname").val()),
        "contacts" : _.escape($("#contacts").val()),
        "email" : _.escape($("#email").val()),
        "facebook" : _.escape($("#facebook").val()),
        "twitter" : _.escape($("#twitter").val())
      },
      success: function(datas) {
        window.location.hash = "#contacts";
      }
    });
    return false;
  }
});

var EditContact = Backbone.View.extend({
  el: "#app",
  template: _.template( $("#editContactTemplate").html() ),
  initialize: function() {
    _.bindAll(this, "render", "data");
  },
  events: {
    'submit form#frmEditContact' : 'editContact'
  },
  render: function(response) {
    $(this.el).html( this.template({ contact: response }) );
  },
  data: function(id) {
    var self = this;
    var contactsCollection = new ContactsCollection();
    contactsCollection.fetch({
      data: { id_edit: id },
      success: function(datas) {
        self.render(datas.toJSON());
      }
    });
  },
  editContact: function() {
    $.ajax({
      type: "post",
      url: "/contacts",
      data: {
        "id" : _.escape($("#id").val()),
        "name" : _.escape($("#fname").val()),
        "contacts" : _.escape($("#contacts").val()),
        "email" : _.escape($("#email").val()),
        "facebook" : _.escape($("#facebook").val()),
        "twitter" : _.escape($("#twitter").val())
      },
      success: function(datas) {
        window.location.hash = "#contacts";
      }
    });
    return false;
  }
});

var Locations = Backbone.Model.extend({
  defaults: {
    name: "",
    latlong: "",
    featured_photo: "",
    death_count: "",
    affected_count: "",
    status_board: "",
    needs: "",
    centers: "",
    status: ""
  }
});

var LocationCollection = Backbone.Collection.extend({
  model: Locations,
  url: "/locations"
});

var LocationView = Backbone.View.extend({
  el: "#app",
  template: _.template( $("#locationTemplate").html() ),
  initialize: function() {
    _.bindAll(this, "render", "locations");
  },
  render: function(response) {
    var self = this;
    $(this.el).html( this.template({ locations: response }) );
  },
  locations: function() {
    var self = this;
    var collection = new LocationCollection();
    collection.fetch({
      success: function(datas) {
        self.render(datas.toJSON());
      }
    });
  }
});

var AddLocation = Backbone.View.extend({
  el: "#app",
  template: _.template( $("#addLocationTemplate").html() ),
  events: {
    'submit form#frmAddLocation': 'addLocation'
  }, 
  render: function() {
    $(this.el).html( this.template );
  },
  addLocation: function() {
    $.ajax({
      type: "post",
      url: "/locations",
      data: {
        "name": _.escape($("#name").val()),
        "latlong": _.escape($("#latlong").val()),
        "featured_photo": _.escape($("#featured_photo").val()),
        "death_count": _.escape($("#death_count").val()),
        "affected_count": _.escape($("#affected_count").val()),
        "status_board": _.escape($("#status_board").val()),
        "food": _.escape($("#food").val()),
        "water": _.escape($("#water").val()),
        "medicines": _.escape($("#medicines").val()),
        "social_workers": _.escape($("#social_workers").val()),
        "medical_workers": _.escape($("#medical_workers").val()),
        "shelter": _.escape($("#shelter").val()),
        "formula": _.escape($("#formula").val()),
        "toiletries": _.escape($("#toiletries").val()),
        "flashlights": _.escape($("#flashlights").val()),
        "cloths": _.escape($("#cloths").val()),
        "power": _.escape($("#status_power").is(':checked')),
        "communication": _.escape($("#status_communication").is(':checked')),
        "status_water": $("#status_water").is(":checked")
      },
      success: function() {
        window.location.hash = "#locations";
      }
    });
    return false;
  }
});

var DistributionView = Backbone.View.extend({
  el: "#app",
  template: _.template( $("#distributionsTemplate").html() ),
  render: function() {
    $(this.el).html( this.template() );
  }
});

var AddDistribution = Backbone.View.extend({
  el: "#app",
  template: _.template( $("#addDistributionsTemplate").html() ),
  initialize: function() {
    _.bindAll(this, "render", "contacts");
  },
  events: {
    "submit form#frmAddDistribution" : "addDistribution"
  },
  render: function(contacts, locs) {
    $(this.el).html( this.template({ contacts: contacts, locations: locs }) );
  },
  contacts: function() {
    var self = this;
    $.ajax({
      type: "get",
      url: "/distributions/fetch",
      success: function(datas) {
        console.log(JSON.parse(datas));
        var dd = JSON.parse(datas);
        self.render(dd.contacts, dd.locations);
      }
    });
  },
  addDistribution: function() {
    $.ajax({
      type: "post",
      url: "/distributions",
      data: {
        "date_of_distribution": _.escape($("#date_of_distribution").val()),
        "contact": _.escape($("#contact").val()),
        "destinations": _.escape($("#destinations").val()),

        "s_food" : $("#chk_supply_goal_food").is(":checked").val(),

        "supply_goal": _.escape($("#supply_goal").val()),
        "actual_supply": _.escape($("#actual_supply").val())
      },
      success: function() {
        window.location.hash = "#distributions";
      }
    });
    return false;
  }
});

var DistributorView = Backbone.View.extend({
  el: "#app",
  template: _.template( $("#distributorsTemplate").html() ),
  render: function() {
    $(this.el).html( this.template() );
  }
});

var AddDistributor = Backbone.View.extend({
  el: "#app",
  template: _.template( $("#addDistributorTemplate").html() ),
  events: {
    "submit form#frmAddDistributor" : "addDistributor"
  },
  initialize: function() {
    _.bindAll(this, "render", "contacts");
  },
  render: function(response, locs) {
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
  },
  addDistributor: function() {
    $.ajax({
      type: "post",
      url: "/distributors",
      data: {
        "name": _.escape($("#fname").val()),
        "location": _.escape($("#location").val()),
        "phone": _.escape($("#phone").val()),
        "email": _.escape($("#email").val()),
        "website": _.escape($("#website").val()),
        "contacts": _.escape($("#contacts").val()),
        "destinations": _.escape($("#destinations").val()),
      },
      success: function() {
        window.location.hash = "#distributors";
      }
    });
    return false;
  }
});

var DropOffCenterView = Backbone.View.extend({
  el: "#app",
  template: _.template( $("#drop-off-centersTemplate").html() ),
  render: function() {
    $(this.el).html( this.template() );
  }
});

var AddDropOffCenter = Backbone.View.extend({
  el: "#app",
  template: _.template( $("#addDrop-off-centersTemplate").html() ),
  events: {
    "submit form#frmAddDropOffCenter" : "addDropOff"
  },
  render: function() {
    $(this.el).html( this.template() );
  },
  addDropOff: function() {
    $.ajax({
      type: "post",
      url: "/drop-off-centers",
      data: {
        "name" : _.escape($("#fname").val()),
        "latlong" : _.escape($("#latlong").val()),
        "destinations" : _.escape($("#destinations").val()),
        "schedule" : _.escape($("#schedule").val()),
        "twitter" : _.escape($("#twitter").val()),
        "facebook" : _.escape($("#facebook").val()),
        "phone" : _.escape($("#phone").val()),
        "email" : _.escape($("#email").val()),
      },
      success: function() {
        window.location.hash = "#drop-off-centers";
      }
    });
    return false;
  }
});

var ResourcesView = Backbone.View.extend({
  el: "#app",
  template: _.template( $("#resourcesTemplate").html() ),
  render: function() {
    $(this.el).html( this.template() );
  }
});

var SubscribersView = Backbone.View.extend({
  el: "#app",
  template: _.template( $("#subscribersTemplate").html() ),
  render: function() {
    $(this.el).html( this.template() );
  }
});

var PostsModel = Backbone.Model.extend({
  defaults: {
    name: "",
    email: "",
    twitter: "",
    facebook: "",
    phone: "",
    message: ""
  }
});

var PostsCollection = Backbone.Collection.extend({
  model: PostsModel,
  url: "/posts"
});

var PostsView = Backbone.View.extend({
  el: "#app",
  template: _.template( $("#postsTemplate").html() ),
  initialize: function() {
    _.bindAll(this, "render", "posts");
  },
  render: function(response) {
    $(this.el).html( this.template({ posts: response}) );
  },
  posts: function() {
    var self = this;
    var collection = new PostsCollection();
    collection.fetch({
      success: function(datas) {
        self.render(datas.toJSON());
      }
    });
  }
});

var AddPost = Backbone.View.extend({
  el: "#app",
  template: _.template( $("#addPostTemplate").html() ),
  events: {
    "submit form#frmAddPost" : "addPost"
  },
  render: function() {
    $(this.el).html( this.template() );
  },
  addPost: function() {
    $.ajax({
      type: "post",
      url: "/posts",
      data: {
        "name": _.escape($("#fname").val()),
        "email": _.escape($("#email").val()),
        "twitter": _.escape($("#twitter").val()),
        "facebook": _.escape($("#facebook").val()),
        "phone": _.escape($("#phone").val()),
        "message": _.escape($("#message").val())
      },
      success: function() {
        window.location.hash = "#posts";
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
        "contact/edit/:id" : "renderEditContactPage",

        "locations" : "renderLocationPage",
        "location/new" : "renderAddLocationPage",

        "distributions" : "renderDistributionPage",
        "distribution/new" : "renderAddDistributionPage",

        "distributors" : "renderDistributorPage",
        "distributor/new" : "renderAddDistributorPage",

        "drop-off-centers" : "renderDropOffCenterPage",
        "drop-off-center/new" : "renderAddDropOffCenterPage",

        "resources" : "renderResourcesPage",

        "subscribers" : "renderSubscriberPage",

        "posts" : "renderPostsPage",
        "post/new" : "renderAddPostPage",

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
      contactView.contacts();
    },
    renderAddContactPage: function() {
      addContact.render();
    },
    renderEditContactPage: function(id) {
      editContact.render();
      editContact.data(id);
    },

    renderLocationPage: function() {
      locationView.render();
      locationView.locations();
    },
    renderAddLocationPage: function() {
      addLocation.render();
    },

    renderDistributionPage: function() {
      distributionView.render();
    },
    renderAddDistributionPage: function() {
      addDistribution.render();
      addDistribution.contacts();
    },

    renderDistributorPage: function() {
      distributorView.render();
    },
    renderAddDistributorPage: function() {
      addDistributor.render();
      addDistributor.contacts();
    },

    renderDropOffCenterPage: function() {
      dropOffCenterView.render();
    },
    renderAddDropOffCenterPage: function() {
      addDropOffCenter.render();
    },

    renderResourcesPage: function() {
      resourcesView.render();
    },

    renderSubscriberPage: function() {
      subscribersView.render();
    },

    renderPostsPage: function() {
      postsView.render();
      postsView.posts();
    },
    renderAddPostPage: function() {
      addPost.render();
    }
    
});

var mainview = new MainView();
var addUser = new AddUser();
var editUser = new EditUser();

var contactView = new ContactView();
var addContact = new AddContact();
var editContact = new EditContact();

var locationView = new LocationView();
var addLocation = new AddLocation();

var distributionView = new DistributionView();
var addDistribution = new AddDistribution();

var distributorView = new DistributorView();
var addDistributor = new AddDistributor();

var dropOffCenterView = new DropOffCenterView();
var addDropOffCenter = new AddDropOffCenter();

var resourcesView = new ResourcesView();

var subscribersView = new SubscribersView();

var postsView = new PostsView();
var addPost = new AddPost();

var router = new Router();
Backbone.history.start();