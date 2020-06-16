<?php
function getOldGetEduroamProfile( $display, $name ) {
	return [
			"id" => "${name}_geteduroam_no",
			"name" => $display,
			"default" => true,
			"eapconfig_endpoint" => "https://geteduroam.no/generate.php",
			"token_endpoint" => "https://geteduroam.no/token.php",
			"authorization_endpoint" => "https://geteduroam.no/authorize.php",
			"oauth" => true,
		];
}

return [
	'versions' => [1/*, 2*/],
	'seq' => intval(file_get_contents(dirname(__DIR__) . DIRECTORY_SEPARATOR . 'serial.txt')),
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
			//10, // 9 Uninett - Uninett
			2223, // 9 Uninett - Test usage (ad.eduroam.no)
			4306, // 9 Uninett - geteduroam
			1052, // 627 CNRS - CERMAV - 500 Internal Server Error
			3830, // 2180 South African eduroam Test IdP - 500 Internal Server Error
		],
	'hiddenInstitutes' => [
			//9, Uninett
		],
	'cacheTime' => 604800,
];
