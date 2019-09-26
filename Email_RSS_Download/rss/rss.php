<?php
// include composer autoload
require 'vendor/autoload.php';
 
use Suin\RSSWriter\Channel;
use Suin\RSSWriter\Feed;
use Suin\RSSWriter\Item;
 
header("Content-type: text/xml");
// init mysql
$db = new MysqliDb (Array(
    'host' => '192.168.50.230',         # MySQL Host IP/name
    'username' => 'test',               # MySQL account
    'password' => 'mysql_password',     # MySQL account password
    'db' => 'test',                     # MySQL Schema name
    'port' => 3307,                     # MySQL Host Port
    'charset' => 'utf8'
));
 
// select database and get latest 10 items
$db->orderBy("id","DESC");
$torrent = $db->get('mail_rss', 10);

// init feed
$feed = new Feed();
 
// Set channel info
$channel = new Channel();
$channel
    ->title("my rss service")
    ->description("cool rss for cool kids")
    ->url('http://xjzz.tk/')
    ->appendTo($feed);
 
for ($i = 1; $i <= count($torrent); $i++) {
    // item
    $item = new Item();
    $item
        ->title($torrent[$i-1]['subject'])
        ->description($torrent[$i-1]['subject'])
        ->url($torrent[$i-1]['content'])
        ->enclosure('', '', 'application/x-bittorrent')
        ->appendTo($channel);
}
 
echo $feed;