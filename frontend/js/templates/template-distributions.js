var Distribution = Backbone.Model.extend({
  defaults: {
    date_of_distribution: "",
    contact: "",
    destinations: "",
    supply_goal: "",
    actual_supply: "",
    images: "",
    status: "",
    info: "",
    featured_photo: ""
  }
});

var DistributionCollection = Backbone.Collection.extend({
  model: Distribution,
  url: "/distributions"
});

var DistributionView = Backbone.View.extend({
  el: "#app",
  template: _.template( $("#distributionsTemplate").html() ),
  initialize: function() {
    _.bindAll(this, "render", "distributions");
  },
  render: function(response) {
    var self = this;
    $(this.el).html( this.template({ distributions: response }) );
    $("#distributionsGrid tr[data-id]").each(function(){
      var id = $(this).attr("data-id");
      $(this).find("a.first").click(function() {
        self.editDistribution(id);
      });
      $(this).find("a.last").click(function() {
        self.deleteDistribution(id);
      });
    });
  },
  distributions: function() {
    var self = this;
    var collection = new DistributionCollection();
    collection.fetch({
      success: function(datas) {
        self.render(datas.toJSON());
      }
    });
  },
  editDistribution: function(id) {
    var route = new Router();
    route.navigate("distribution/edit/" + id, {trigger: true});
  },
  deleteDistribution: function(id) {
    if (confirm("Are you sure to delete?")) {
      var collection = new DistributionCollection();
      collection.fetch({
        data: { id_delete: id },
        success: function(data) {
          $('#distributionsGrid tr[data-id="' + id + '"]').fadeOut('fast');
        },
        error: function() {
          $('#distributionsGrid tr[data-id="' + id + '"]').fadeOut('fast');
        }
      });
    }
  }
});

var AddDistribution = Backbone.View.extend({
  el: "#app",
  template: _.template( $("#addDistributionsTemplate").html() ),
  initialize: function() {
    _.bindAll(this, "render", "contacts");
  },
  events: {
    "submit form#frmAddDistribution" : "addDistribution"
  },
  render: function(contacts, locs) {
    $(this.el).html( this.template({ contacts: contacts, locations: locs }) );
  },
  contacts: function() {
    var self = this;
    $.ajax({
      type: "get",
      url: "/distributions/fetch",
      success: function(datas) {
        var dd = JSON.parse(datas);
        self.render(dd.contacts, dd.locations);
      }
    });
  },
  addDistribution: function() {
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
      url: "/distributions",
      data: {
        "image_urls" : JSON.stringify(obj_image_url),
        "image_titles" : JSON.stringify(obj_image_title),
        "image_captions" : JSON.stringify(obj_image_caption),
        "date_of_distribution": _.escape($("#date_of_distribution").val()),
        "contact": _.escape($("#contact").val()),
        "destinations": _.escape($("#destinations").val()),
        "status" : _.escape($("#status").val()),
        "info": _.escape($("#info").val()),
        "featured_photo": _.escape($("#featured_photo").val()),
        "description": _.escape($("#description").val()),

        // supply goal
        "chk_supply_goal_food" : _.escape($("#supply_goal_food").val()),
        "chk_supply_goal_food_description" : _.escape($("#supply_goal_food_description").val()),

        "chk_supply_goal_water" : _.escape($("#supply_goal_water").val()),
        "chk_supply_goal_water_description" : _.escape($("#supply_goal_water_description").val()),

        "chk_supply_goal_medicines" : _.escape($("#supply_goal_medicines").val()),
        "chk_supply_goal_medicines_description" : _.escape($("#supply_goal_medicines_description").val()),

        "chk_supply_goal_social_workers" : _.escape($("#supply_goal_social_workers").val()),
        "chk_supply_goal_social_workers_description" : _.escape($("#supply_goal_social_workers_description").val()),

        "chk_supply_goal_medical_workers" : _.escape($("#supply_goal_medical_workers").val()),
        "chk_supply_goal_medical_workers_description" : _.escape($("#supply_goal_medical_workers_description").val()),

        "chk_supply_goal_shelter" : _.escape($("#supply_goal_shelter").val()),
        "chk_supply_goal_shelter_description" : _.escape($("#supply_goal_shelter_description").val()),

        "chk_supply_goal_formula" : _.escape($("#supply_goal_formula").val()),
        "chk_supply_goal_formula_description" : _.escape($("#supply_goal_formula_description").val()),

        "chk_supply_goal_toiletries" : _.escape($("#supply_goal_toiletries").val()),
        "chk_supply_goal_toiletries_description" : _.escape($("#supply_goal_toiletries_description").val()),

        "chk_supply_goal_flashlights" : _.escape($("#supply_goal_flashlights").val()),
        "chk_supply_goal_flashlights_description" : _.escape($("#supply_goal_flashlights_description").val()),

        // actual supply
        "chk_actual_supply_food" : _.escape($("#actual_supply_food").val()),
        "chk_actual_supply_food_description" : _.escape($("#actual_supply_food_description").val()),

        "chk_actual_supply_water" : _.escape($("#actual_supply_water").val()),
        "chk_actual_supply_water_description" : _.escape($("#actual_supply_water_description").val()),

        "chk_actual_supply_medicines" : _.escape($("#actual_supply_medicines").val()),
        "chk_actual_supply_medicines_description" : _.escape($("#actual_supply_medicines_description").val()),

        "chk_actual_supply_social_workers" : _.escape($("#actual_supply_social_workers").val()),
        "chk_actual_supply_social_workers_description" : _.escape($("#actual_supply_social_workers_description").val()),

        "chk_actual_supply_medical_workers" : _.escape($("#actual_supply_medical_workers").val()),
        "chk_actual_supply_medical_workers_description" : _.escape($("#actual_supply_medical_workers_description").val()),

        "chk_actual_supply_shelter" : _.escape($("#actual_supply_shelter").val()),
        "chk_actual_supply_shelter_description" : _.escape($("#actual_supply_shelter_description").val()),

        "chk_actual_supply_formula" : _.escape($("#actual_supply_formula").val()),
        "chk_actual_supply_formula_description" : _.escape($("#actual_supply_formula_description").val()),

        "chk_actual_supply_toiletries" : _.escape($("#actual_supply_toiletries").val()),
        "chk_actual_supply_toiletries_description" : _.escape($("#actual_supply_toiletries_description").val()),

        "chk_actual_supply_flashlights" : _.escape($("#actual_supply_flashlights").val()),
        
        "chk_actual_supply_flashlights_description" : _.escape($("#actual_supply_flashlights_description").val())
      },
      success: function() {
        window.location.hash = "#distributions";
      }
    });
    return false;
  }
});

var EditDistribution = Backbone.View.extend({
  el: "#app",
  template: _.template( $("#editDistributionsTemplate").html() ),
  initialize: function() {
    _.bindAll(this, "render", "contacts");
  },
  render: function() {
    $(this.el).html( this.template() );
  },
  contacts: function() {
    var self = this;
    $.ajax({
      type: "get",
      url: "/distributions/fetch",
      success: function(datas) {
        var dd = JSON.parse(datas);
        self.render(dd.contacts, dd.locations);
      }
    });
  }
});