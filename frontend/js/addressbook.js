var Authenticate = Backbone.Model.extend({
  defaults: {
    email: "",
    password: ""
  },
  urlRoot: "/login"
});

var RegisterModel = Backbone.Model.extend({
  defaults: {
    email: "",
    password: "",
    name: ""
  },
  urlRoot: "/register"
});

var MainView = Backbone.View.extend({
  el: "#maincontent",
  template: _.template( $("#loginTemplate").html() ),
  render: function() {
    $(this.el).html( this.template() );
  },
  events: {
    "submit form.frmlogin" : "login"
  },
  login: function() {
    var email = $("#email").val();
    var password = $("#password").val();

    var authenticate = new Authenticate();
    authenticate.save({ email: _.escape(email), password: _.escape(password) }, {
      success: function(datas) {
        console.log(datas.toJSON());
        var data = datas.toJSON();
        if (data.success == false) {
          $("#notification").show();
          $("#notification").removeClass("alert-success");
          $("#notification").addClass("alert-danger");
          $(".type").text("Error!");
          $(".message").text(data.message);
        } else {
          $("#notification").show();
          $("#notification").removeClass("alert-danger");
          $("#notification").addClass("alert-success");
          $(".type").text("Wohoo!");
          $(".message").text(data.message);

          setTimeout(function() {
            $(".type").text("");
            $(".message").text("Redirecting...");
            window.location = "/dashboard";
          }, 2000);
        }
      },
      error: function() {
        console.log("Not authenticated!");
      }
    });
    return false;
  }
});

var RegisterView = Backbone.View.extend({
  el: "#maincontent",
  template: _.template( $("#registerTemplate").html() ),
  render: function() {
    $(this.el).html( this.template() );
  },
  events: {
    "submit form.frmRegister" : "register"
  },
  register: function() {
    var email = $("#email").val();
    var password = $("#password").val();
    var name = $("#name").val();

    var register = new RegisterModel();
    register.save({ email: _.escape(email), password: _.escape(password), name: _.escape(name) }, {
      success: function(datas) {
        console.log(datas.toJSON());
        var data = datas.toJSON();
        if (data.success == false) {
          $("#notification").show();
          $("#notification").removeClass("alert-success");
          $("#notification").addClass("alert-danger");
          $(".type").text("Error!");
          $(".message").text(data.message);
        } else {
          $("#notification").show();
          $("#notification").removeClass("alert-danger");
          $("#notification").addClass("alert-success");
          $(".type").text("Well done!");
          $(".message").text(data.message);

          setTimeout(function() {
            $(".type").text("");
            $(".message").text("Redirecting...");
            window.location = "/dashboard";
          }, 2000);

        }
      },
      error: function() {
        console.log("Failed to register!");
      }
    });
    return false;
  }
});

var Router = Backbone.Router.extend({
    routes: {
        "" : "renderMainPage",
        "register" : "renderRegisterPage",
        "*default" : "defaultpage"
    },
    renderMainPage: function() {
      mainView.render();
    },
    renderRegisterPage: function() {
      registerView.render();
    },
    defaultpage: function(d) {
      var html = "<div class=\"alert alert-dismissable alert-warning\"><button type=\"button\" class=\"close\" data-dismiss=\"alert\">&times;</button><strong>ERROR!</strong> Unhandled route<p>No access granted for: <strong>\"" + d + "\"</strong></p></div>"
      $("#content").html(html);
    }
});

var router = new Router();
var mainView = new MainView();
var registerView = new RegisterView();
Backbone.history.start();