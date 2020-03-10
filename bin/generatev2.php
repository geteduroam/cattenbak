#!/usr/bin/env php
<?php
chdir(__DIR__);
extract( require '../etc/cattenbak.conf.php' );
require '../src/_autoload.php';

@mkdir('../disco');
@mkdir('../disco/v2');


function toJson($data) {
	return json_encode($data, JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES|JSON_UNESCAPED_UNICODE) . "\n";
}
function idpSorter($a,$b) {
	return $a['cat_idp'] - $b['cat_idp'];
}

$cat = new eduroam\CAT\CAT( 'https://cat.eduroam.org/user/API.php', $cacheTime );
foreach($languages as $language) {
	@mkdir("../disco/v2/$language");
	$idps2 = [];
	$data2 = [
		'version' => 2,
		'seq' => $seq,
		'lang' => $language,
	];
	$instances2 = [];
	foreach($countries as $country) {
		$idps2 += eduroam\CAT\IdentityProvider::getIdentityProvidersByCountry($cat, $country, $language);
	}
	foreach($idps2 as $idp) {
		if (in_array($idp->getEntityID(), $hiddenInstitutes, true)) continue;
		$profiledata2 = [
			'version' => 2,
			'seq' => $seq,
			'lang' => $language,
			'provider' => $id,
		];
		$id = "cat_" . $idp->getEntityID();
		$profiles = array_key_exists( $idp->getEntityID(), $getEduroamProfiles )
			? $geProfiles[$idp->getEntityID()]
			: []
			;
		foreach($idp->getProfiles() as $profile) {
			if (in_array($profile->getProfileID(), $hiddenProfiles, true) || $profile->isSilverBullet() || $profile->isRedirect()) continue;
			$profiles[] = [
				'id' => 'cat_' . $profile->getProfileID(),
				'name' => $profile->getDisplay(),
				'eapconfig_endpoint' => $profile->getDevice('eap-config')->getDownloadLink(),
				'oauth' => false,
			];
		}
		$instances2[] = [
			'name' => $idp->getTitle(),
			'country' => $idp->getCountry(),
			'keywords' => array_key_exists( $idp->getEntityID(), $keywords ) ? $keywords[$idp->getEntityID()] : [],
			'file' => "provider-$id-$seq.json",
		];
		$profiledata2['profiles'] = $profiles;
		file_put_contents("../disco/v2/$language/provider-$id-$seq.json", toJson($profiledata2));
	}
	$data2['instances'] = $instances2;
	file_put_contents("../disco/v2/$language/discovery-$seq.json", toJson($data2));
}

error_log(sprintf('Total requests: %s', $cat->getRequestCount()));
error_log(sprintf('Cache hits: %s', $cat->getRequestCount() - $cat->getUncachedRequestCount()));
error_log(sprintf('Network hits: %s', $cat->getUncachedRequestCount()));
