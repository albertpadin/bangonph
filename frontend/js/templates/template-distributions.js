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
        "chk_supply_goal_food" : _.escape($("#chk_supply_goal_food").val()),
        "chk_supply_goal_water" : _.escape($("#chk_supply_goal_water").val()),
        "chk_supply_goal_medicines" : _.escape($("#chk_supply_goal_medicines").val()),
        "chk_supply_goal_social_workers" : _.escape($("#chk_supply_goal_social_workers").val()),
        "chk_supply_goal_medical_workers" : _.escape($("#chk_supply_goal_medical_workers").val()),
        "chk_supply_goal_shelter" : _.escape($("#chk_supply_goal_shelter").val()),
        "chk_supply_goal_formula" : _.escape($("#chk_supply_goal_formula").val()),
        "chk_supply_goal_toiletries" : _.escape($("#chk_supply_goal_toiletries").val()),
        "chk_supply_goal_flashlights" : _.escape($("#chk_supply_goal_flashlights").val()),

        // actual supply
        "chk_actual_supply_food" : _.escape($("#chk_actual_supply_food").val()),
        "chk_actual_supply_water" : _.escape($("#chk_actual_supply_water").val()),
        "chk_actual_supply_medicines" : _.escape($("#chk_actual_supply_medicines").val()),
        "chk_actual_supply_social_workers" : _.escape($("#chk_actual_supply_social_workers").val()),
        "chk_actual_supply_medical_workers" : _.escape($("#chk_actual_supply_medical_workers").val()),
        "chk_actual_supply_shelter" : _.escape($("#chk_actual_supply_shelter").val()),
        "chk_actual_supply_formula" : _.escape($("#chk_actual_supply_formula").val()),
        "chk_actual_supply_toiletries" : _.escape($("#chk_actual_supply_toiletries").val()),
        "chk_actual_supply_flashlights" : _.escape($("#chk_actual_supply_flashlights").val())
      },
      success: function() {
        window.location.hash = "#distributions";
      }
    });
    return false;
  }
});