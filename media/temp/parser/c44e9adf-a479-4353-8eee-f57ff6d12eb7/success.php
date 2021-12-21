<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">

<head>
    <title>
        Thank you! Your order was accepted!
    </title>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <meta name="viewport" content="width=320" />
    <meta name="MobileOptimized" content="width=320" />
    <link href='http://fonts.googleapis.com/css?family=Roboto+Condensed&subset=latin,cyrillic' rel='stylesheet' type='text/css'>
    <link href='http://fonts.googleapis.com/css?family=Lobster&subset=latin,cyrillic' rel='stylesheet' type='text/css'>
    <link media="all" rel="stylesheet" type="text/css" href="http://cdn.leadbit.com/success/css/order-style.css" />
    
    



                        <!-- Facebook Pixel Code -->
                        <script>
                        !function(f,b,e,v,n,t,s)
                        {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
                        n.callMethod.apply(n,arguments):n.queue.push(arguments)};
                        if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
                        n.queue=[];t=b.createElement(e);t.async=!0;
                        t.src=v;s=b.getElementsByTagName(e)[0];
                        s.parentNode.insertBefore(t,s)}(window, document,'script',
                        'https://connect.facebook.net/en_US/fbevents.js');
                        fbq('init', '<?= $_GET["px"] ?>');
                        fbq('track', 'Lead');
                        fbq('track', 'AddToCart');
                        fbq('track', 'Purchase', {value: 0.00, currency: 'USD'});
                        fbq('track', 'SubmitApplication');
                        fbq('track', 'Contact');
                        </script>
                        <!-- End Facebook Pixel Code -->
                        <style>body{margin:0;color:#fff;font:17px/25px Georgia,"Times New Roman",Times,serif;background:#1f242a;min-width:446px}img{border-style:none}a{text-decoration:none;color:#a82720}a:hover{text-decoration:underline}input,select,textarea{font:100% Georgia,"Times New Roman",Times,serif;vertical-align:middle;color:#000;outline:0}fieldset,form{margin:0;padding:0;border-style:none}q{quotes:none}q:before{content:}q:after{content:}#wrapper{width:100%;overflow:hidden;padding:50px 0}.container{width:440px;margin:0 auto;display:block;position:relative}.order-block{width:440px;border:4px dashed #fcca49;border-radius:30px;height:auto;margin:0 auto;position:relative;text-align:center;font-size:20px;line-height:30px;overflow:hidden;color:#d5e5eb}.order-block:after{display:block;clear:both;content:}.decoration{background:url(../img/order-page-decoration.png) no-repeat;width:24px;height:32px;position:absolute;left:-23px;top:336px}.order-block .text-holder{padding:20px}.order-block h2{font:35px/35px Lobster,Arial,Helvetica,sans-serif;margin:0 0 59px;color:#fff}.order-block h2 span{display:block;font-size:45px;line-height:45px;color:#fcca49;margin:0 0 -2px}.order-block p{margin:0 0 18px}.order-block .text-box{bottom:20px;font-size:20px;line-height:30px;color:#1f242a;left:3px;width:100%;box-sizing:border-box;background:#fcca49;padding:20px}.order-block .text-box h2{font-size:35px;line-height:40px;color:#1f242a;margin:0 0 32px}.order-block .text-box h2 span{font-size:45px;line-height:45px;color:#ae1d1d;display:block;margin:-6px 0 0}.order-form{overflow:hidden}.order-form .text{background:url(../img/bg-order-page-text.png) no-repeat;width:253px;height:42px;float:left}.order-block .text-box p{margin:0 0 18px}.order-form .text input{background:0 0;border:none;width:227px;height:40px;float:left;font-size:16px;line-height:40px;color:#726033;padding:10px 13px 12px}.btn-save{border:none;background:url(../img/order-page-btn-save.png) no-repeat;width:129px;height:40px;float:right;font:20px/40px "Roboto Condensed",Arial,Helvetica,sans-serif;text-transform:uppercase;color:#fff;float:right;padding:0 0 2px;margin:0;cursor:pointer}</style></head>
                        

<body>
<div id="wrapper">
    <div class="container">
        <span class="decoration">
        </span>
        <div class="order-block">
            <div class="text-holder">
                <h2><span>Thank you! </span> Your order was accepted!</h2>
                <p>Our operator will contact you to confirm the order. <br /> Delivery provided by a courier service. Payment - upon delivery!</p>
            </div>
            <div class="text-box">
                <h2>
                    Participate in the <span>sale promotion.</span>
                </h2>
                <p>
                    To participate in the sale and monitor your order status, enter E-mail and press "Save".
                </p>
                <form class="order-form" id="email_form" action="success.html#">
                    <fieldset>
                        <div class="text">
                            <input type="email" id="email" placeholder="Enter your e-mail..." name="email">
                        </div>
                        <input data-error="Enter your e-mail"  data-success="Thank you for participating! Your E-mail has been saved!" class="btn-save" type="submit" value="Save">
                    </fieldset>

                </form>
            </div>

        </div>
    </div>

</div>
</body>

</html>