<html>
<head>
<title>Test {{ title }}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="../css/base.css">

<!-- BRYTHON -->
<link rel="pythonpath" href="../lib" hreflang="py" />
<script src="../lib/source-map/dist/source-map.min.js"></script>
<script src="../lib/brython/www/src/brython_dist.js"></script>

<script type="text/python">

{{ test }}

from browser import document as doc, html
doc <= html.SPAN(id='finished')
</script>

<script>
var onLoadHandler = function() {
        brython({'debug':1,'profile':2,'profile_start':false});
};
</script>

</head>

<!-- 3. Display the application -->
<body onload="onLoadHandler()">
    <div id='test'>
    {{ content }}
    </div>
</body>

</html>


