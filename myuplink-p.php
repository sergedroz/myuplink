<html>
<head>
<Title>myuplink tokens</title>
</head>
<body>
<?php 

$a = explode("&", $_SERVER['QUERY_STRING'] );
foreach ($a as $line ) {
    $b = explode( "=", str_replace("%20", " ", $line) );
    echo "<pre>$b[0]: $b[1]</pre>";
}
?>

</body>
</html>

