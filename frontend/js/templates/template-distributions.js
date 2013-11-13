var Distribution = Backbone.Model.extend({
  defaults: {
    date_of_distribution: "",
    contact: "",
    destinations: "",
    supply_goal: "",
    actual_supply: ""
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
    $(this.el).html( this.template({ distributions: response }) );
  },
  distributions: function() {
    var self = this;
    var collection = new DistributionCollection();
    collection.fetch({
      success: function(datas) {
        self.render(datas.toJSON());
      }
    });
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
    $.ajax({
      type: "post",
      url: "/distributions",
      data: {
        "date_of_distribution": _.escape($("#date_of_distribution").val()),
        "contact": _.escape($("#contact").val()),
        "destinations": _.escape($("#destinations").val()),

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

        "chk_actual_supply_flashlights" : _.escape($("#actual_supply_flashlights").val())
        "chk_actual_supply_flashlights_description" : _.escape($("#actual_supply_flashlights_description").val())
      },
      success: function() {
        window.location.hash = "#distributions";
      }
    });
    return false;
  }
});