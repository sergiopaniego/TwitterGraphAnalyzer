var url = window.location.href.split('/');
if (url[url.length-1] == 'graph') {
    var element = document.getElementById("ordinary");
    element.classList.add("active");
} else {
    var element = document.getElementById(url[url.length-1]);
    element.classList.add("active");
}

$('li').click(function() {
    $('li > a').removeClass();
    $(this).children('a').addClass('active');
});