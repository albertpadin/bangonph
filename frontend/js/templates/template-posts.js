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