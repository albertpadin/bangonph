var Locations = Backbone.Model.extend({
  defaults: {
    name: "",
    latlong: "",
    featured_photo: "",
    death_count: "",
    death_count_text: "",
    affected_count: "",
    affected_count_text: "",
    status_board: "",
    needs: "",
    centers: "",
    status: "",
    images: "",
    hash_tag: ""
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
    $("#locationsGrid tr[data-id]").each(function(){
      var id = $(this).attr("data-id");
      $(this).find("a.first").click(function() {
        self.editLocation(id);
      });
      $(this).find("a.last").click(function() {
        self.deleteLocation(id);
      });
    });
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
  editLocation: function(id) {
    var route = new Router();
    route.navigate("location/edit/" + id, {trigger: true});
  },
  deleteLocation: function(id) {
    if (confirm("Are you sure to delete?")) {
      var collection = new LocationCollection();
      collection.fetch({
        data: { id_delete: id },
        success: function(data) {
          $('#locationsGrid tr[data-id="' + id + '"]').fadeOut('fast');
        },
        error: function() {
          $('#locationsGrid tr[data-id="' + id + '"]').fadeOut('fast');
        }
      });
    }
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
    var obj_image_url = [];
    $(".image_url").each(function() {
        obj_image_url.push({"src": $(this).val()});
    });

    var obj_image_title = [];
    $(".image_title").each(function() {
        obj_image_title.push({"image_title": $(this).val()});
    });
    
    var obj_image_caption = [];
    $(".image_caption").each(function() {
        obj_image_caption.push({"image_caption": $(this).val()});
    });
    $.ajax({
      type: "post",
      url: "/locations",
      data: {
        "image_urls" : JSON.stringify(obj_image_url),
        "image_titles" : JSON.stringify(obj_image_title),
        "image_captions" : JSON.stringify(obj_image_caption),
        "name": _.escape($("#name").val()),
        "latlong": _.escape($("#latlong").val()),
        "featured_photo": _.escape($("#featured_photo").val()),
        "death_count": _.escape($("#death_count").val()),
        "death_count_text": _.escape($("#death_count_text").val()),
        "affected_count": _.escape($("#affected_count").val()),
        "affected_count_text": _.escape($("#affected_count_text").val()),
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
        "miscellaneous": _.escape($("#miscellaneous").val()),
        "power": _.escape($("#status_power").val()),
        "communication": _.escape($("#status_communication").val()),
        "status_water": _.escape($("#status_water").val()),
        "status_medicines": _.escape($("#status_medicines").val()),
        "status_clothes": _.escape($("#status_clothes").val()),
        "status_foods": _.escape($("#status_foods").val()),
        "status_shelter": _.escape($("#status_shelter").val()),
        "hash_tag" : _.escape($("#hash_tag").val())
      },
      success: function() {
        window.location.hash = "#locations";
      }
    });
    return false;
  }
});

var EditLocation =  Backbone.View.extend({
  el: "#app",
  template: _.template( $("#editLocationTemplate").html() ),
  events: {
    'submit form#frmEditLocation': 'editLocation'
  }, 
  initialize: function() {
    _.bindAll(this, "render", "location");
  },
  render: function(response) {
    $(this.el).html( this.template({ location: response }) );
  },
  location: function(id) {
    console.log(id);
    var self = this;
    var collection = new LocationCollection();
    collection.fetch({
      data: { id_edit: id },
      success: function(data) {
        self.render(data.toJSON());
      }
    });
  },
  editLocation: function() {
    var obj_image_url = [];
    $(".image_url").each(function() {
        obj_image_url.push({"src": $(this).val()});
    });

    var obj_image_title = [];
    $(".image_title").each(function() {
        obj_image_title.push({"image_title": $(this).val()});
    });
    
    var obj_image_caption = [];
    $(".image_caption").each(function() {
        obj_image_caption.push({"image_caption": $(this).val()});
    });
    $.ajax({
      type: "post",
      url: "/locations",
      data: {
        "id": $("#id").val(),
        "image_urls" : JSON.stringify(obj_image_url),
        "image_titles" : JSON.stringify(obj_image_title),
        "image_captions" : JSON.stringify(obj_image_caption),
        "name": _.escape($("#name").val()),
        "latlong": _.escape($("#latlong").val()),
        "featured_photo": _.escape($("#featured_photo").val()),
        "death_count": _.escape($("#death_count").val()),
        "death_count_text": _.escape($("#death_count_text").val()),
        "affected_count": _.escape($("#affected_count").val()),
        "affected_count_text": _.escape($("#affected_count_text").val()),
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
        "miscellaneous": _.escape($("#miscellaneous").val()),
        "power": _.escape($("#status_power").val()),
        "communication": _.escape($("#status_communication").val()),
        "status_water": _.escape($("#status_water").val()),
        "status_medicines": _.escape($("#status_medicines").val()),
        "status_clothes": _.escape($("#status_clothes").val()),
        "status_foods": _.escape($("#status_foods").val()),
        "status_shelter": _.escape($("#status_shelter").val()),
        "hash_tag" : _.escape($("#hash_tag").val())
      },
      success: function() {
        window.location.hash = "#locations";
      }
    });
    return false;
  }
});