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
    var self = this;
    $(this.el).html( this.template({ posts: response}) );
    $("#postsGrid tr[data-id]").each(function(){
      var id = $(this).attr("data-id");
      $(this).find("a.first").click(function() {
        self.editPost(id);
      });
      $(this).find("a.last").click(function() {
        self.deletePost(id);
      });
    });
  },
  posts: function() {
    var self = this;
    $(".loading-message").show();
    var collection = new PostsCollection();
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
  editPost: function(id) {
    var route = new Router();
    route.navigate("post/edit/" + id, {trigger: true});
  },
  deletePost: function(id) {
    if(confirm("Are you sure to delete?")) {
      var collection = new PostsCollection();
      collection.fetch({
        data: {id_delete: id},
        success: function() {
          $('#postsGrid tr[data-id="' + id + '"]').fadeOut('fast');
        },
        error: function() {
          $('#postsGrid tr[data-id="' + id + '"]').fadeOut('fast');
        }
      });
    }
  }
});

var AddPost = Backbone.View.extend({
  el: "#app",
  template: _.template( $("#addPostTemplate").html() ),
  events: {
    "submit form#frmAddPost" : "addPost"
  },
  initialize: function() {
    _.bindAll(this, "render", "locations");
  },
  render: function(response) {
    $(this.el).html( this.template({ locations: response}) );
  },
  locations: function() {
    var self = this;
    var collection = new LocationCollection();
    collection.fetch({
      success: function(datas) {
        self.render(datas.toJSON());
      }
    });
  },
  addPost: function() {
    var need_transpo = "";
    var need_people = "";
    var need_goods = "";
    var need_needs = "";
    var have_transpo = "";
    var have_people = "";
    var have_goods = "";
    var have_needs = "";

    if($("#post_type_need_transpo").is(":checked")) {
      need_transpo = $("#post_type_need_transpo").val();
    }
    if($("#post_type_need_people").is(":checked")) {
      need_people = $("#post_type_need_people").val();
    }
    if($("#post_type_need_goods").is(":checked")) {
      need_goods = $("#post_type_need_goods").val();
    }
    if($("#post_type_need_needs").is(":checked")) {
      need_needs = $("#post_type_need_needs").val();
    }
    if($("#post_type_have_transpo").is(":checked")) {
      have_transpo = $("#post_type_have_transpo").val();
    }
    if($("#post_type_have_people").is(":checked")) {
      have_people = $("#post_type_have_people").val();
    }
    if($("#post_type_have_goods").is(":checked")) {
      have_goods = $("#post_type_have_goods").val();
    }
    if($("#post_type_have_needs").is(":checked")) {
      have_needs = $("#post_type_have_needs").val();
    }

    $.ajax({
      type: "post",
      url: "/posts",
      data: {
        "name": _.escape($("#name").val()),
        "email": _.escape($("#email").val()),
        "twitter": _.escape($("#twitter").val()),
        "facebook": _.escape($("#facebook").val()),
        "phone": _.escape($("#phone").val()),
        "message": _.escape($("#message").val()),
        "need_transpo": need_transpo,
        "need_people": need_people,
        "need_goods": need_goods,
        "need_needs": need_needs,
        "have_transpo": have_transpo,
        "have_people": have_people,
        "have_goods": have_goods,
        "have_needs": have_needs,
        "expiry": _.escape($("#expiry").val()),
        "location": _.escape($("#location").val())
      },
      success: function() {
        window.location.hash = "#posts";
      }
    });
    return false;
  }
});

var EditPost = Backbone.View.extend({
  el: "#app",
  template: _.template( $("#editPostTemplate").html() ),
  events: {
    "submit form#frmEditPost" : "editPost"
  },
  initialize: function() {
    _.bindAll(this, "render", "post");
  },
  render: function() {
    $(this.el).html( this.template() );
  },
  post: function(id) {
    var self = this;
    $(".loading-message").show();
    var collection = new PostsCollection();
    collection.fetch({
      data: {id_edit: id},
      success: function(data) {
        $(".loading-message").fadeOut("fast");
        self.render(data.toJSON());
      }
    });
  }
});