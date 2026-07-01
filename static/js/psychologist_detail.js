$(document).ready(function() {
    
    // چک کردن اینکه پلاگین لود شده است
    if (typeof $.fn.starRating === 'undefined') {
        console.error("پلاگین starRating لود نشده است!");
        return;
    }

    $(".my-rating-2").starRating({
        readOnly: true,
        totalStars: 5,
        starSize: 35,
        starShape: 'rounded',
        emptyColor: 'lightgray',
        hoverColor: '#f1c40f',
        activeColor: '#f1c40f',
        strokeWidth: 0,
        useGradient: false
    });
});