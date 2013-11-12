var FC = Backbone.Model.extend({
  urlRoot: "/datas"
});

var FollowModel = Backbone.Model.extend({
  defaults: {
    email: ""
  },
  urlRoot: "/follow"
});

var UnFollowModel = Backbone.Model.extend({
  defaults: {
    email: ""
  },
  urlRoot: "/unfollow"
});

var MainView = Backbone.View.extend({
  el: "#maincontent",
  template: _.template( $("#mainTemplate").html() ),
  initiliaze: function() {
    _.bindAll(this, "render", "datas");
  },
  render: function(response) {
    var self = this;
    $(this.el).html( this.template({ FC : response }) );
    $("#fc_content a.follow[data-id]").each(function(){
      var id = $(this).attr("data-id");
      $(this).click(function() {
        self.follow(id);
        $(this).text("Unfollow");
        $(this).removeClass("follow");
        $(this).addClass("unfollow");
      });
    });
    $("#fc_content a.unfollow[data-id]").each(function(){
      var id = $(this).attr("data-id");
      $(this).click(function() {
        self.unfollow(id);
        $(this).text("Follow");
        $(this).removeClass("unfollow");
        $(this).addClass("follow");
      });
    });
  },
  datas: function() {
    var self = this;
    var fc = new FC();
    fc.fetch({
      success: function(datas) {
        console.log(datas.toJSON());
        self.render(datas.toJSON());
      },
      error: function() {
        console.log("Failed to retrieve!");
      }
    });
  },
  follow: function(id) {
    var followModel = new FollowModel();
    followModel.save({ email: _.escape(id) }, {
      success: function(datas) {
        console.log(datas.toJSON());
      },
      error: function() {
        console.log("Failed to follow!");
      }
    });
  },
  unfollow: function(id) {
    var unfollowModel = new UnFollowModel();
    Backbone.ajax({
      url: unfollowModel.url() + "/" + id,
      success: function(datas) {
        console.log(datas);
      }
    });
  }
});

var FollowersView = Backbone.View.extend({
  el: "#maincontent",
  template: _.template( $("#followersTemplate").html() ),
  render: function() {
    $(this.el).html( this.template() );
  }
});

var Router = Backbone.Router.extend({
  routes: {
      "" : "renderMainPage",
      "following" : "renderFollowersPage",
      "*default" : "defaultpage"
  },
  renderMainPage: function() {
    mainView.render();
    mainView.datas();
  },
  renderFollowersPage: function() {
    followersView.render();
  },
  defaultpage: function(d) {
    var html = "<div class=\"alert alert-dismissable alert-warning\"><button type=\"button\" class=\"close\" data-dismiss=\"alert\">&times;</button><strong>ERROR!</strong> Unhandled route<p>No access granted for: <strong>\"" + d + "\"</strong></p></div>"
    $("#maincontent").html(html);
  }
});

var router = new Router();
var mainView = new MainView();
var followersView = new FollowersView();
Backbone.history.start();