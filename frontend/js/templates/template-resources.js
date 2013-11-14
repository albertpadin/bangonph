var ResourcesView = Backbone.View.extend({
  el: "#app",
  template: _.template( $("#resourcesTemplate").html() ),
  render: function() {
    $(this.el).html( this.template() );
  }
});

var SubscribersView = Backbone.View.extend({
  el: "#app",
  template: _.template( $("#subscribersTemplate").html() ),
  render: function() {
    $(this.el).html( this.template() );
  }
});