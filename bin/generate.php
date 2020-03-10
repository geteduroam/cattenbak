#!/usr/bin/env php
<?php
chdir(__DIR__);
require '../src/_autoload.php';

$app = new \eduroam\Cattenbak\CattenbakApp();
$gen1 = new \eduroam\Cattenbak\V1Generator( $app );

$gen1->write();

error_log(sprintf('Total requests: %s', $app->getCAT()->getRequestCount()));
error_log(sprintf('Cache hits: %s', $app->getCAT()->getRequestCount() - $app->getCAT()->getUncachedRequestCount()));
error_log(sprintf('Network hits: %s', $app->getCAT()->getUncachedRequestCount()));
