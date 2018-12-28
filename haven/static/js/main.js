var $ = require('jquery');
global.jQuery = $;
global.$ = $;
require('django-formset');

$(function() {
  $("form .formset tbody tr").formset({
    addText: '<i class="fas fa-plus"></i> Add more',
    addCssClass: 'add-row btn btn-sm btn-outline-secondary',
  });
});
