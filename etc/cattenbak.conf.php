<?php return [
	//'catnip' => 'https://y1wtfr5sqa.execute-api.eu-central-1.amazonaws.com/catnip',
	'versions' => [1/*, 2*/],
	'countries' => [], /* list countries to query, or keep empty for all */
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
		],
	'getEduroamProfiles' => [
			6635 => [
				[
					'id' => 'emergya_geteduroam_no_cat_2618',
					'name' => 'eduroam Visitor Access (eVA)',
					'eapconfig_endpoint' => 'https://pade.nl/eva.eap-config',
					'token_endpoint' => 'https://emergya.geteduroam.no/oauth/token/',
					'authorization_endpoint' => 'https://emergya.geteduroam.no/oauth/authorize/',
					'oauth' => true,
				],
				[
					'id' => 'pade_tmp',
					'name' => 'Pade',
					'eapconfig_endpoint' => 'https://pade.nl/hostedidp-geteduroam.eap-config',
				],
				[
					"id" => 'error_geteduroam_no',
					"name" => 'I Am Error',
					"eapconfig_endpoint" => 'https://geteduroam.app/',
				],
			],
		],
	'hiddenProfiles' => [
			//10, // 9 Uninett - Uninett, test
			7734, // 9 Unnamed Entity - Al-Maktoum College of Higher Education, 500 Internal Server Error from CAT
		],
	'hiddenInstitutes' => [
			//9, Uninett, test
		],
	'cacheTime' => 1800,
];
