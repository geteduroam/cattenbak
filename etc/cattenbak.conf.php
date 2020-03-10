<?php return [
	'versions' => [1, 2],
	'seq' => 9,
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
	'getEduroamProfiles' => [
		9 => [
				[
					"id" => "geteduroam_no",
					"name" => "Mobile Device",
					"default" => true,
					"eapconfig_endpoint" => "https://geteduroam.no/generate.php",
					"token_endpoint" => "https://geteduroam.no/token.php",
					"authorization_endpoint" => "https://geteduroam.no/authorize.php",
					"oauth" => true,
				],
			],
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
