<?php
    /* 
    Leadbit.com API
    25.06.2020
     */

    /*
    You need to change:
        {token} - token
        {flow_hash} - Tracking URL hash
        {landing} - Landing page
        {referrer} - Referrer
        {phone} - Phone
        {name} - Name
        {country} - Country code
        {address} - Address
        {email} - Email
        {lastname} - Last Name
        {comment} - Comment
        {layer} - Layer page
        {ip} - IP address
        {sub1} - Sub1
        {sub2} - Sub2
        {sub3} - Sub3
        {sub4} - Sub4
        {sub5} - Sub5
    */
    if (!empty($_POST['phone'])) {
        send_the_order ($_POST);
    }
    function send_the_order ($post){
        $params=array(
            'flow_hash' => 'BMBk',
            'landing' => $post['landing'],
            'referrer' => $_SERVER['HTTP_REFERER'],
            'phone' => $post['phone'],
            'name' => $post['name'],
            'country' => $post['country'],
            'country' => 'at',
            'address' => $post['address'],
            'email' => $post['email'],
            'lastname' => $post['lastname'],
            'comment' => $post['comment'],
            'layer' => $post['layer'],
            'ip' => $_SERVER['REMOTE_ADDR'],
            'sub1' => $post['sub1'],  // Метка баера
            'sub2' => $post['sub2'],  // ID клика
            'sub3' => $post['sub3'],
            'sub4' => $post['sub4'],  // FB Pixel
            'sub5' => $post['sub5'],  
        );
        $url = 'http://wapi.leadbit.com/api/new-order/_5f882f4d15d39208580935';
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
        curl_setopt($ch, CURLOPT_FOLLOWLOCATION, 1);
        curl_setopt($ch, CURLOPT_USERAGENT, $_SERVER['HTTP_USER_AGENT']);
        curl_setopt($ch, CURLOPT_REFERER, $url);
        curl_setopt($ch, CURLOPT_POST, 1);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $params);
        $return= curl_exec($ch);
        curl_close($ch);
        $array=json_decode($return, true);
        header('Location: success.php?px='.$_POST['sub4']);
    }