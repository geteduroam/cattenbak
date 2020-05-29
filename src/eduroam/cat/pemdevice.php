<?php declare(strict_types=1);

/*
 * This file is part of the PHP eduroam CAT client
 * A client to download data from https://cat.eduroam.org/
 *
 * Copyright: 2018-2020, Jørn Åne de Jong, Uninett AS <jorn.dejong@uninett.no>
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

namespace eduroam\CAT;

/**
 * A subclass of Device that returns only the certificate as a PEM.
 * It will behave identical to EAP config, except for that it will
 * not return the XML data from CAT verbatim, but parse the eap-config
 * and return only the PEM certificate.
 *
 * A disadvantage of using PEM is that any other settings, such as
 * EAP types or proxy settings are lost, but these days these tend
 * to be the same for different institutions anyway.
 */
class PemDevice extends Device
{
	/**
	 * Construct a new lazy loaded device.
	 *
	 * @param CAT    $cat       CAT instance
	 * @param int    $idpID     Identity provider ID
	 * @param int    $profileID Profile ID
	 * @param string $deviceID  Device ID (eap-config)
	 * @param string $lang      Language
	 */
	public function __construct( CAT $cat, int $idpID, int $profileID, string $deviceID, string $lang = '' )
	{
		\assert( 'eap-config' === $deviceID, 'PEM device must have $deviceID to be eap-config' );
		parent::__construct( $cat, $idpID, $profileID, 'eap-config', $lang );
	}

	/**
	 * Get the ID of this device as it is stored in the CAT database.
	 *
	 * Since this is a constructed device, we prepend the x- prefix
	 * to the constructed name of the device, "pem"
	 *
	 * @return string The device ID
	 */
	public function getDeviceID(): string
	{
		return 'x-pem';
	}

	/**
	 * Get the friendly name for this device.
	 *
	 * This is always the string 'CA certificate (PEM)'
	 *
	 * @return string 'CA certificate (PEM)'
	 */
	public function getDisplay(): string
	{
		return 'eduroam CA certificate (PEM)';
	}

	/**
	 * Get message explaining what this class provides.
	 *
	 * Since CAT doesn't support downloading the PEM directly,
	 * it doesn't have a Device type for it and doesn't have a default
	 * description.  This method is thus overridden to provide a
	 * description that is displayed on the webpage.
	 *
	 * @return string Plaintext message, safe to put in HTML
	 */
	public function getMessage(): string
	{
		return 'This option allows an experienced user to get the CA certificate used by this institutions RADIUS server, in order to configure eduroam manually.  Note that any EAP and proxy settings are not included, and you may need to contact your institution to ask about those.';
	}

	/**
	 * Get message explaining who this profile is meant for.
	 *
	 * Since CAT doesn't support downloading the PEM directly,
	 * it doesn't have a Device type for it and doesn't have a default
	 * informational text.  This method is thus overridden to provide a
	 * description that is displayed on the webpage.
	 *
	 * @return string Plaintext message, safe to put in HTML
	 */
	public function getDeviceInfo()
	{
		return 'No instructions are provided for this option, as this is option only meant for experienced users that are able to configure eduroam on their devices themselves.';
	}

	/**
	 * Get the download link for this device.
	 *
	 * The "download link" for the certificate does not exist, because
	 * CAT doesn't offer a possibility to download only the certificate.
	 * A way to solve this would be to make a new endpoint that returns
	 * only the certificate, but for now this function will simply
	 * return a data URL that a webbrowser could show as a download.
	 *
	 * @return string Data URL containing all certificates
	 */
	public function getDownloadLink(): string
	{
		return 'data:application/x-x509-ca-cert;base64,' . \base64_encode( \implode( "\n", $this->getCertificates() ) );
	}

	/**
	 * Return all CA certificates for the current profile as PEM.
	 *
	 * Retrieves the EAP configuration XML from CAT using the standard
	 * API, and parses it to return all certificates that it finds.
	 * Duplicate certificates are removed.
	 *
	 * The result is an array of PEM-format certificates, which consists
	 * of a start string, base64 encoded certificate and end string.
	 * The result can be converted to a .pem file simply by
	 * concatination.
	 *
	 * @return string[] array of certificates in PEM format
	 */
	public function getCertificates(): array
	{
		$certificates = [];
		$methods = $this->cat->getEapConfig( $this->getProfileID() )->EAPIdentityProvider->AuthenticationMethods;
		foreach ( $methods->AuthenticationMethod as $method ) {
			foreach ( $method->ServerSideCredential->CA as $ca ) {
				$encoded = "-----BEGIN CERTIFICATE-----\n"
					. \implode( "\n", \str_split( $ca->__toString(), 64 ) )
					. "\n-----END CERTIFICATE-----\n";
				if ( !\in_array( $encoded, $certificates, true ) ) {
					$certificates[] = $encoded;
				}
			}
		}

		return $certificates;
	}
}
