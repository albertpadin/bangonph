var AddressBook = Backbone.Model.extend({
  defaults: {
    fullname: "",
    email: "",
    phone: "",
    address: ""
  }
});

var AddressBookCollection = Backbone.Collection.extend({
  model: AddressBook,
  url: "/addressbook"
});

var SearchCollection = Backbone.Collection.extend({
  model: AddressBook,
  url: function() {
    return "/addressbook/search/" + this.searchTerm;
  }
});

var MainView = Backbone.View.extend({
  el: "#app",
  template: _.template( $("#mainTemplate").html() ),
  initialize: function() {
    _.bindAll(this, "render", "lists");
  },
  events: {
    'submit form#frmSearch' : 'searchAddressBook'
  },
  render: function(response) {
    console.log(response);
    // var stooges = response;
    // console.log(_.pluck(stooges, "fullname"));
    var self = this;
    $(this.el).html( this.template({ addressbook: response }) );
    $("#contactsGrid tr[data-id]").each(function(){
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
  lists: function() {
    var self = this;
    var collection = new AddressBookCollection();
    collection.fetch({
      success: function(datas) {
        self.render(datas.toJSON());
      },
      error: function() {
        console.log("Failed!");
      }
    });
  },
  editContact: function(id) {
    var route = new Router();
    route.navigate("edit/" + id, {trigger: true});
  },
  deleteContact: function(id, name) {
    if (confirm("Are you sure to delete?")) {
      var collection = new AddressBookCollection();
      collection.fetch({
        data: { id_delete: id },
        success: function(data) {
          console.log(data.toJSON());
          $('#contactsGrid tr[data-id="' + id + '"]').fadeOut('fast');
          $(".success-message").fadeIn("fast");
          $("#title").text('"' + name + '" has been successfully deleted.');
        },
        error: function() {
          $(".error-message").fadeIn("fast");
          $("#title").text('Unable to delete "' + name + '". Try again.');
        }
      });
    }
  },
  searchAddressBook: function() {
    var self = this;
    var input = $("#search").val();
    var collection = new SearchCollection();
    collection.searchTerm = _.escape(input);
    collection.fetch({
      success: function(datas) {
        self.render(datas.toJSON());
      }
    });
    return false;
  }
});

var AddView = Backbone.View.extend({
  el: "#app",
  template: _.template( $("#newTemplate").html() ),
  events: {
    'submit form#frmAdd': 'addAddressBook'
  }, 
  render: function() {
    $(this.el).html( this.template );
  },
  addAddressBook: function(event) {
    var fname = $("#fname").val();
    var email = $("#email").val();
    var phone = $("#phone").val();
    var address = $("#address").val();

    if (fname == null || fname == "") {
      $(".fname").fadeIn("fast");
      $("#fname").focus();
      return false;
    }
    if (email == null || email == "") {
      $(".email").fadeIn("fast");
      $("#email").focus();
      return false;
    }
    if (phone == null || phone == "") {
      $(".phone").fadeIn("fast");
      $("#phone").focus();
      return false;
    }
    if (address == null || address == "") {
      $(".address").fadeIn("fast");
      $("#address").focus();
      return false;
    }

    var details = {
      fullname: _.escape(fname),
      email: _.escape(email),
      phone: _.escape(phone),
      address: _.escape(address)
    };

    var collection = new AddressBookCollection();
    collection.create(details, {
      success: function(data) {
        window.location.hash = "#";
        console.log(data.toJSON());
        $(".fname").hide();
        $(".email").hide();
        $(".phone").hide();
        $(".address").hide();

        $("#fname").val("");
        $("#email").val("");
        $("#phone").val("");
        $("#address").val("");
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

var EditView = Backbone.View.extend({
  el: "#app",
  template: _.template( $("#editTemplate").html() ),
  initialize: function() {
    _.bindAll(this, "render", "list");
  },
  events: {
    'submit form#frmEdit' : 'editAddressBook'
  },
  render: function(response) {
    console.log(response);
    $(this.el).html( this.template({ addressbook: response }) );
  },
  list: function(id) {
    var self = this;
    var collection = new AddressBookCollection();
    collection.fetch({
      data: { id_edit: id },
      success: function(data) {
        self.render(data.toJSON());
      }
    });
  },
  editAddressBook: function() {
    var id = $("#id").val();
    var fname = $("#fname").val();
    var email = $("#email").val();
    var phone = $("#phone").val();
    var address = $("#address").val();

    var details = {
      id: id,
      fullname: _.escape(fname),
      email: _.escape(email),
      phone: _.escape(phone),
      address: _.escape(address)
    };

    var collection = new AddressBookCollection();
    collection.create(details, {
      success: function(data) {
        window.location.hash = "#";
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

var Router = Backbone.Router.extend({
    routes: {
        "" : "renderMainPage",
        "new" : "renderNewAddressBook",
        "edit/:id" : "renderEditAddressBook",
        "*default" : "defaultpage"
    },

    defaultpage: function(d) {
      var html = "<div class='error-route'><strong>ERROR:</strong> Unhandled route</div>";
      html += 'No access granted for: <strong>"' + d + '"</strong>';
      $("#app").html(html);
    },

    renderMainPage: function() {
      mainview.render();
      mainview.lists();
      mainview.searchAddressBook();
    },

    renderNewAddressBook: function() {
      addView.render();
    },

    renderEditAddressBook: function(id) {
      editView.render();
      editView.list(id);
    }
    
});

var mainview = new MainView();
var addView = new AddView();
var editView = new EditView();
var router = new Router();
Backbone.history.start();