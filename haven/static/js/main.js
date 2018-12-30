var $ = require('jquery');
global.jQuery = $;
global.$ = $;
require('django-formset');
require('bootstrap-checkbox');

$(function() {
  $("form .formset tbody tr").formset({
    addText: '<i class="fas fa-plus"></i> Add more',
    addCssClass: 'add-row btn btn-sm btn-outline-secondary',
  });

  $(":checkbox").checkboxpicker();
});
