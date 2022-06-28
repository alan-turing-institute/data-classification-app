var $ = require('jquery');
global.jQuery = $;
global.$ = $;
require('django-formset');
require('bootstrap-checkbox');
require('bootstrap/js/dist/collapse');
require('bootstrap/js/dist/dropdown');

global.formset = function(selector, prefix, addText){
  $(function() {
    var options = {};

    options.prefix = prefix;

    if (addText) {
      options.addText = '<i class="fas fa-plus"></i> ' + addText;
      options.addCssClass = 'add-row btn btn-sm btn-outline-secondary';
    }

    $(selector).find(".formset tbody tr").formset(options);
  });
}
