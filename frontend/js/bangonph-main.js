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
        "location/edit/:id" : "renderEditLocationPage",

        "distributions" : "renderDistributionPage",
        "distribution/new" : "renderAddDistributionPage",
        "distribution/edit/:id" : "renderEditDistributionPage",

        "distributors" : "renderDistributorPage",
        "distributor/new" : "renderAddDistributorPage",
        "distributor/edit/:id" : "renderEditDistributorPage",

        "drop-off-centers" : "renderDropOffCenterPage",
        "drop-off-center/new" : "renderAddDropOffCenterPage",
        "drop-off-center/edit/:id" : "renderEditDropOffCenterPage",

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
    renderEditLocationPage: function(id) {
      editLocation.render();
      editLocation.location(id);
    },

    renderDistributionPage: function() {
      distributionView.render();
      distributionView.distributions();
    },
    renderAddDistributionPage: function() {
      addDistribution.render();
      addDistribution.contacts();
    },
    renderEditDistributionPage: function(id) {
      editDistribution.render();
      editDistribution.datas(id);
    },

    renderDistributorPage: function() {
      distributorView.render();
      distributorView.distributors();
    },
    renderAddDistributorPage: function() {
      addDistributor.render();
    },
    renderEditDistributorPage: function(id){
      editDistributor.render();
      editDistributor.data(id);
    },

    renderDropOffCenterPage: function() {
      dropOffCenterView.render();
      dropOffCenterView.drops();
    },
    renderAddDropOffCenterPage: function() {
      addDropOffCenter.render();
    },
    renderEditDropOffCenterPage: function(id) {
      editDropOffCenter.render();
      editDropOffCenter.dropoff(id);
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
var editLocation = new EditLocation();

var distributionView = new DistributionView();
var addDistribution = new AddDistribution();
var editDistribution = new EditDistribution();

var distributorView = new DistributorView();
var addDistributor = new AddDistributor();
var editDistributor = new EditDistributor();

var dropOffCenterView = new DropOffCenterView();
var addDropOffCenter = new AddDropOffCenter();
var editDropOffCenter = new EditDropOffCenter();

var resourcesView = new ResourcesView();

var subscribersView = new SubscribersView();

var postsView = new PostsView();
var addPost = new AddPost();

var router = new Router();
Backbone.history.start();