var $ = require('jquery');
global.jQuery = $;
global.$ = $;
require('django-formset');
require('bootstrap-checkbox');
require('bootstrap/js/dist/collapse');
require('bootstrap/js/dist/dropdown');

$(function() {
  $("form:not(.remove-add-button) .formset tbody tr").formset({
    addText: '<i class="fas fa-plus"></i> Add more',
    addCssClass: 'add-row btn btn-sm btn-outline-secondary',
  });

  // If the form is of class remove-add-button then we do not add the "Add more" button
  $("form.remove-add-button .formset tbody tr").formset({
  });

  $(":checkbox").checkboxpicker();
});
