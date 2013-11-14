var DropOff = Backbone.Model.extend({
  defaults: {
    name: "",
    drop_off_locations: "",
    distributor: "",
    address: "",
    latlong: "",
    destinations: "",
    schedule: "",
    twitter: "",
    facebook: "",
    contacts: "",
    email: ""
  }
});

var DropOffCollection = Backbone.Collection.extend({
  model: DropOff,
  url: "/drop-off-centers"
});

var DropOffCenterView = Backbone.View.extend({
  el: "#app",
  template: _.template( $("#drop-off-centersTemplate").html() ),
  initialize: function() {
    _.bindAll(this, "render", "drops");
  },
  render: function(response) {
    var self = this;
    $(this.el).html( this.template({ dropoffcenters: response }) );
    $("#dropOffGrid tr[data-id]").each(function(){
      var id = $(this).attr("data-id");
      $(this).find("a.first").click(function() {
        self.editDrop(id);
      });
      $(this).find("a.last").click(function() {
        self.deleteDrop(id);
      });
    });
  },
  drops: function() {
    var self = this;
    $(".loading-message").show();
    var collection = new DropOffCollection();
    collection.fetch({
      success: function(datas) {
        $(".loading-message").fadeOut("fast");
        self.render(datas.toJSON());
      }
    });
  },
  editDrop: function(id) {
    var route = new Router();
    route.navigate("drop-off-center/edit/" + id, {trigger: true});
  },
  deleteDrop: function(id) {
    if (confirm("Are you sure to delete?")) {
      var collection = new DropOffCollection();
      collection.fetch({
        data: { id_delete : id },
        success: function() {
          $('#dropOffGrid tr[data-id="' + id + '"]').fadeOut('fast');
        },
        error: function() {
          $('#dropOffGrid tr[data-id="' + id + '"]').fadeOut('fast');
        }
      });
    }
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
        "name" : _.escape($("#name").val()),
        "drop_off_locations" : _.escape($("#drop_off_locations").val()),
        "distributors" : _.escape($("#distributors").val()),
        "address" : _.escape($("#address").val()),
        "latlong" : _.escape($("#latlong").val()),
        "destinations": _.escape($("#destinations").val()),
        "schedule" : _.escape($("#schedule").val()),
        "twitter" : _.escape($("#twitter").val()),
        "facebook" : _.escape($("#facebook").val()),
        "contacts" : _.escape($("#contacts").val()),
        "email" : _.escape($("#email").val())
      },
      success: function() {
        window.location.hash = "#drop-off-centers";
      }
    });
    return false;
  }
});

var EditDropOffCenter = Backbone.View.extend({
  el: "#app",
  template: _.template( $("#editDrop-off-centersTemplate").html() ),
  events: {
    "submit form#frmEditDropOffCenter" : "editDropOff"
  },
  initialize: function() {
    _.bindAll(this, "render", "dropoff");
  },
  render: function(response) {
    $(this.el).html( this.template({ drop: response }) );
  },
  dropoff: function(id) {
    var self = this;
    var collection = new DropOffCollection();
    collection.fetch({
      data: { id_edit : id },
      success: function(datas) {
        self.render(datas.toJSON());
      }
    });
  },
  editDropOff: function() {
    $.ajax({
      type: "post",
      url: "/drop-off-centers",
      data: {
        "id" : $("#id").val(),
        "name" : _.escape($("#name").val()),
        "drop_off_locations" : _.escape($("#drop_off_locations").val()),
        "distributors" : _.escape($("#distributors").val()),
        "address" : _.escape($("#address").val()),
        "latlong" : _.escape($("#latlong").val()),
        "destinations": _.escape($("#destinations").val()),
        "schedule" : _.escape($("#schedule").val()),
        "twitter" : _.escape($("#twitter").val()),
        "facebook" : _.escape($("#facebook").val()),
        "contacts" : _.escape($("#contacts").val()),
        "email" : _.escape($("#email").val())
      },
      success: function() {
        window.location.hash = "#drop-off-centers";
      }
    });
    return false;
  }
});