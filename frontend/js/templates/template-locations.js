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