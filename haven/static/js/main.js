var $ = require('jquery');
global.jQuery = $;
global.$ = $;
require('django-formset');
require('bootstrap-checkbox');
require('bootstrap/js/dist/collapse');
require('bootstrap/js/dist/dropdown');

global.formset = function(selector, prefix, show_add_button){
  $(function() {
    var options = {};

    options.prefix = prefix;

    if (show_add_button) {
      options.addText = '<i class="fas fa-plus"></i> Add more';
      options.addCssClass = 'add-row btn btn-sm btn-outline-secondary';
    }

    $(selector).find(".formset tbody tr").formset(options);
  });
}

$(function() {
  $(":checkbox").not(".formset :checkbox").checkboxpicker();
});
