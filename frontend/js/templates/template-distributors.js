var Distributor = Backbone.Model.extend({
  defaults: {
    name: "",
    contact_num: "",
    location: "",
    email: "",
    website: "",
    contacts: "",
    facebook: ""
  }
});

var DistributorCollection = Backbone.Collection.extend({
  model: Distributor,
  url: "/distributors"
});

var DistributorView = Backbone.View.extend({
  el: "#app",
  template: _.template( $("#distributorsTemplate").html() ),
  initialize: function() {
    _.bindAll(this, "render", "distributors")
  },
  render: function(response) {
    var self = this;
    $(this.el).html( this.template({ distributors: response }) );
    $('#distributorsGrid tr[data-id]').each(function(){
      var id = $(this).attr("data-id");
      $(this).find("a.first").click(function(){
        self.editDistributor(id);
      });
      $(this).find('a.last').click(function(){
        self.deleteDistributor(id);
      });
    });
  },
  distributors: function(){
    var self = this;
    var distributorsCollection = new DistributorCollection();
    distributorsCollection.fetch({
      success: function(datas){
        self.render(datas.toJSON());
      }
    });

  },
  deleteDistributor: function(id){
    if ( confirm('Are you sure to delete?')) {
      
     var collection = new DistributorCollection();
      collection.fetch({
        data: { id_delete: id },
        success: function(data) {
          
          $(".success-message").hide();
          $(".error-message").fadeIn("fast");
          $("#title").text('Unable to delete. Try again.');
        },
        error: function() {
          $('#distributorsGrid tr[data-id="' + id + '"]').fadeOut('fast');
          $(".error-message").hide();
          $(".success-message").fadeIn("fast");
          $("#title").text('Successfully deleted.');
        }
      });

    }
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
        "contact_num": _.escape($("#contact_num").val()),
        "location": _.escape($("#location").val()),
        "email": _.escape($("#email").val()),
        "website": _.escape($("#website").val()),
        "contacts": _.escape($("#contacts").val()),
        "facebook": _.escape($("#facebook").val())
      },
      success: function() {
        window.location.hash = "#distributors";
      }
    });
    return false;
  }
});