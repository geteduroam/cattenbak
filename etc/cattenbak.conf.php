<?php
function getOldGetEduroamProfile( $display, $name ) {
	return [
			"id" => "${name}_geteduroam_no",
			"name" => $display,
			"default" => true,
			"eapconfig_endpoint" => "https://demo.eduroam.no/generate.php",
			"token_endpoint" => "https://demo.eduroam.no/token.php",
			"authorization_endpoint" => "https://demo.eduroam.no/authorize.php",
			"oauth" => true,
		];
}

return [
	'catnip' => 'https://y1wtfr5sqa.execute-api.eu-central-1.amazonaws.com/catnip',
	'versions' => [1/*, 2*/],
	'countries' => ['AL', 'AM', 'AR', 'AT', 'AU', 'BE', 'BG', 'BR', 'CA', 'CH', 'CL', 'CO', 'CR', 'CZ', 'DE', 'DK', 'EC', 'EE', 'ES', 'FI', 'FR', 'GE', 'GEANT', 'GR', 'HR', 'HU', 'IE', 'IL', 'IS', 'IT', 'JP', 'KR', 'LK', 'LT', 'LU', 'LV', 'MA', 'ME', 'MK', 'MT', 'MW', 'MX', 'MY', 'NG', 'NL', 'NO', 'NZ', 'OM', 'PE', 'PH', 'PK', 'PL', 'PT', 'RS', 'RU', 'SE', 'SG', 'SI', 'SK', 'TR', 'UA', 'UG', 'UK', 'US', 'UY', 'ZA'],
	'languages' => ['en', 'nb', 'es', 'de' /*, 'nl' */],
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
				'id' => 'extra_nordunet',
				'name' => 'NORDUnet',
				'country' => 'DK',
				'cat_id' => NULL,
				'profiles' => [getOldGetEduroamProfile('geteduroam provided by Uninett', 'nordu')],
			],
		],
	'getEduroamProfiles' => [
			1643 => [getOldGetEduroamProfile('geteduroam provided by Uninett', 'sunet')],
		],
	'hiddenProfiles' => [
			//10, // 9 Uninett - Uninett, test
			7734, // 9 Unnamed Entity - Al-Maktoum College of Higher Education, 500 Internal Server Error from CAT
		],
	'hiddenInstitutes' => [
			//9, Uninett, test
		],
	'cacheTime' => 604800,
];
