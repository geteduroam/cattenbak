<?php
function geteduroamProfile( $name ) {
	return [
			"id" => "${name}_geteduroam_no",
			"name" => "geteduroam",
			"default" => true,
			"eapconfig_endpoint" => "https://geteduroam.no/generate.php",
			"token_endpoint" => "https://geteduroam.no/token.php",
			"authorization_endpoint" => "https://geteduroam.no/authorize.php",
			"oauth" => true,
		];
}


return [
	'versions' => [1, 2],
	'seq' => 10,
	'countries' => ['NO', 'ES', 'NL', 'SE', 'DK', 'FI', 'IS'],
	'languages' => ['en', 'nb', 'es' /*, 'nl' */],
	'keywords' => [
			74 => ['NTNU', 'Trondheim'],
			176 => ['Tromso', 'Tromsø'],
			178 => ['Lillehammer', 'inn'],
			180 => ['uia'],
			275 => ['hin'],
			297 => ['uio', 'Oslo'],
		],
	'extraIdps' => [
			[
				'name' => 'NORDUnet',
				'country' => 'DK',
				'cat_id' => NULL,
				'profiles' => [geteduroamProfile('nordu')],
			],
		],
	'getEduroamProfiles' => [
			9 => [geteduroamProfile('uninett')],
			1643 => [geteduroamProfile('sunet')],
		],
	'hiddenProfiles' => [
			//10, // 9 Uninett Uninett
			//2223, // 9 Uninett Test usage (ad.eduroam.no)
			4306, // 9 Uninett geteduroam
		],
	'hiddenInstitutes' => [
			//9, Uninett
		],
	'cacheTime' => 604800,
];
