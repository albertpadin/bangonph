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
    $(".failed-message").hide();
    $(".loading-message").show();
    var contactsCollection = new ContactsCollection();
    contactsCollection.fetch({
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
    $(".failed-message").hide();
    $(".loading-message").show();
    var contactsCollection = new ContactsCollection();
    contactsCollection.fetch({
      data: { id_edit: id },
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