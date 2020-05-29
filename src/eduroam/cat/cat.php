<?php declare(strict_types=1);

/*
 * This file is part of the PHP eduroam CAT client
 * A client to download data from https://cat.eduroam.org/
 *
 * Copyright: 2018-2020, Jørn Åne de Jong, Uninett AS <jorn.dejong@uninett.no>
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

namespace eduroam\CAT;

use DomainException;

/**
 * cURL wrapper around the CAT API.
 */
class CAT
{
	const CACHE_HASH_FUNCTION = 'sha256';

	/**
	 * Base URL for CAT API.
	 *
	 * @var string
	 */
	protected $base;

	/**
	 * Amount of seconds answers from CAT API are cached.
	 * Note that profile downloads are always initiated by the client
	 * and therefore never cached server-side.
	 *
	 * @var int
	 */
	protected $cache;

	/**
	 * cURL handle
	 *
	 * @var null|resource
	 */
	private $ch = null;

	/**
	 * Count how many requests have been done, including requests that hit the cache
	 *
	 * @var int
	 */
	private $requestCount = 0;

	/**
	 * Count how many requests have been done, excluding requests that hit the cache
	 *
	 * @var int
	 */
	private $uncachedRequestCount = 0;

	/**
	 * Construct a new CAT API object.
	 *
	 * @param string $base  Base URL for CAT API
	 * @param int    $cache Amount of seconds answers from CAT API are cached
	 */
	public function __construct( $base = 'https://cat.eduroam.org/user/API.php', $cache = 1800 )
	{
		$parse = \parse_url( $base );
		if ( \strpos( $base, '?' ) || false === $parse || isset( $parse['fragment'] ) || !isset( $parse['host'] ) ) {
			throw new DomainException( 'Malformed URL' );
		}
		$this->base = $base;
		$this->cache = (int)$cache;
	}

	/**
	 * Get the base URL for CAT API.
	 *
	 * @return string Base URL for CAT API
	 */
	public function getBase(): string
	{
		return $this->base;
	}

	/**
	 * List all identity providers.
	 *
	 * @see https://github.com/GEANT/CAT/blob/master/tutorials/UserAPI.md
	 *
	 * @param string $lang Desired language for friendly strings
	 *
	 * @return array array of tuples {"entityID","title","country","geo","icon","idp"}. geo and icon are optional. idp is provided for conformance reasons, but is just a copy of entityID
	 */
	public function listAllIdentityProviders( $lang = '' ): array
	{
		return $this->catJSONQueryArray( [
			'action' => 'listAllIdentityProviders',
		], $lang, 1800 );
	}

	/**
	 * List identity providers by country.
	 *
	 * @see https://github.com/GEANT/CAT/blob/master/tutorials/UserAPI.md
	 *
	 * @param string $country 2-letter ISO code in caps representing the country, for example <code>NO</code>
	 * @param string $lang    Desired language for friendly strings
	 *
	 * @return array array of tuples: {"idp", "display"}
	 */
	public function listIdentityProviders( $country, $lang = '' ): array
	{
		return $this->catJSONQuery( [
			'action' => 'listIdentityProviders',
			'federation' => $country,
		], $lang, 1800 )->data;
	}

	/**
	 * Get all profiles for an identity provider.
	 *
	 * @see https://github.com/GEANT/CAT/blob/master/tutorials/UserAPI.md
	 *
	 * @param mixed  $idpID
	 * @param string $lang  Desired language for friendly strings
	 *
	 * @return array Array of tuples: {"profile", "display", "idp_name", "logo"}. logo can be 0 or 1 and shows if logo is available
	 */
	public function listProfiles( $idpID, $lang = '' ): array
	{
		return $this->catJSONQuery( [
			'action' => 'listProfiles',
			'idp' => (string)$idpID,
		], $lang )->data;
	}

	/**
	 * Get attributes for a profile, these include support information, description and devices, but not the name.
	 *
	 * @see https://github.com/GEANT/CAT/blob/master/tutorials/UserAPI.md
	 *
	 * @param int    $profileID The ID number of the profile in the CAT database
	 * @param string $lang      Desired language for friendly strings
	 *
	 * @return \stdClass Array of tuples: {"local_email","local_phone","local_url","description","devices"}. All local_ entries and description are optional. devices is an array of touples {"id","display","status","redirect", "eap_customtext","device_customtext"}
	 */
	public function profileAttributes( $profileID, $lang = '' ): \stdClass
	{
		return $this->catJSONQuery( [
			'action' => 'profileAttributes',
			'profile' => (string)$profileID,
		], $lang )->data;
	}

	/**
	 * Ensure that an installer is generated for the profile and operating system combination.
	 * Must be run at least once before the user downloads, but it's not needed to do this every time.
	 * The built-in caching mechanism of this class should take care of that.
	 *
	 * @see https://github.com/GEANT/CAT/blob/master/tutorials/UserAPI.md
	 *
	 * @param string $osName    Name of the operating system as presented in the CAT database (w10, mobileconfig12, linux)
	 * @param int    $profileID The ID number of the profile in the CAT database
	 * @param string $lang      Desired language for friendly strings
	 *
	 * @return \stdClass array of touples {"profile","device","link", "mime"}
	 */
	public function generateInstaller( $osName, $profileID, $lang = '' ): \stdClass
	{
		return $this->catJSONQuery( [
			'action' => 'generateInstaller',
			'device' => $osName,
			'profile' => (string)$profileID,
		], $lang )->data;
	}

	/**
	 * List the devices just like #profileAttributes(int, string), but without custom texts.
	 *
	 * @see https://github.com/GEANT/CAT/blob/master/tutorials/UserAPI.md
	 *
	 * @param int    $profileID The ID number of the profile in the CAT database
	 * @param string $lang      Desired language for friendly strings
	 *
	 * @return array array of touples {"device","display","status","redirect", "eap_customtext","device_customtext"}
	 */
	public function listDevices( $profileID, $lang = '' ): array
	{
		return $this->catJSONQuery( [
			'action' => 'listDevices',
			'profile' => (string)$profileID,
		], $lang )->data;
	}

	/**
	 * Show device information, undocumented CAT feature.
	 *
	 * This feature is mentioned on the cat-users mailing list by Tomaz and
	 * Stefan, and returns CAT-issued HTML messages per device.
	 *
	 * From a comment in the source code, we learn that the "id" field is actually called "device"
	 * https://github.com/GEANT/CAT/blob/898d021beaff1c96398c05517089a979140e6617/web/user/API.php#L166
	 *
	 * The API also asks for a Profile ID, but it doesn't seem like this makes
	 * any difference in the outcome of the API call.
	 *
	 * @param string $osName    Name of the operating system as presented in the CAT database (w10, mobileconfig12, linux)
	 * @param int    $profileID The ID number of the profile in the CAT database
	 * @param string $lang      Desired language for friendly strings
	 *
	 * @return string Device info as HTML text
	 */
	public function getDeviceInfo( $osName, $profileID, $lang = '' ): string
	{
		return $this->executeCatQuery( [
			'action' => 'deviceInfo',
			'device' => $osName,
			'profile' => (string)$profileID,
		], $lang, 'text/html' );
	}

	/**
	 * Generate a direct URL to an installer.
	 *
	 * The installer is always generated by the API endpoint that
	 * is also used by this class.  However, for simplicity reasons,
	 * the URL is not called by this class, but instead forwarded to
	 * the end user.
	 *
	 * @param string $osName    Name of the operating system as presented in the CAT database (w10, mobileconfig12, linux)
	 * @param int    $profileID The ID number of the profile in the CAT database
	 *
	 * @return string The URL to the installer
	 */
	public function getDownloadInstallerURL( $osName, $profileID ): string
	{
		$this->generateInstaller( $osName, $profileID );

		return $this->getCatURL( [
			'action' => 'downloadInstaller',
			'device' => $osName,
			'profile' => (string)$profileID,
		] );
	}

	/**
	 * Retrieve the EAP configuration.
	 *
	 * This is the eap-config "profile" from CAT, which is also used
	 * by the Android installer.  It is the canonical form of a profile
	 * as it is stored in CAT.
	 *
	 * @param int    $profileID The ID number of the profile in the CAT database
	 * @param string $lang      Desired language for friendly strings
	 *
	 * @return \SimpleXMLElement Root element of the EAP-config
	 */
	public function getEapConfig( int $profileID, $lang = '' ): \SimpleXMLElement
	{
		$result = \simplexml_load_string(
			$this->executeCatQuery( [
				'action' => 'downloadInstaller',
				'device' => 'eap-config',
				'profile' => (string)$profileID,
			], $lang, 'application/eap-config', \min( 60, $this->cache ) )
			// Short timeout on cache, when certificate changes on CAT,
			// it must change here as well.
		);
		if ( false === $result ) {
			throw new \DomainException( "eap-config profile ${profileID} is not valid XML" );
		}

		return $result;
	}

	/**
	 * Count how many requests have been issues, including requests that hit the cache
	 *
	 * @return int Amount of requests
	 */
	public function getRequestCount(): int
	{
		return $this->requestCount;
	}

	/**
	 * Count how many requests have been issues, excluding requests that hit the cache
	 *
	 * @return int Amount of requests
	 */
	public function getUncachedRequestCount(): int
	{
		return $this->uncachedRequestCount;
	}

	/**
	 * Get contents by URL through cURL.
	 *
	 * @param string $url    URL to retrieve
	 * @param string $accept Expected content type
	 * @param array  $opts   cURL options as documented on http://php.net/curl_setopt
	 *
	 * @return string Document body
	 */
	protected function file_get_contents_curl( string $url, string $accept = 'application/json', array $opts = [] ): string
	{
		if ( !$this->ch ) {
			$ch = \curl_init();
			if ( false === $ch ) {
				throw new \RuntimeException( 'Unable to initialize cURL' );
			}
			$this->ch = $ch;
		}

		\curl_setopt( $this->ch, \CURLOPT_AUTOREFERER, true );
		\curl_setopt( $this->ch, \CURLOPT_HEADER, 0 );
		\curl_setopt( $this->ch, \CURLOPT_RETURNTRANSFER, 1 );
		\curl_setopt( $this->ch, \CURLOPT_URL, $url );
		\curl_setopt( $this->ch, \CURLOPT_FAILONERROR, true );
		\curl_setopt( $this->ch, \CURLOPT_HTTPHEADER, [
			'Accept: ' . $accept,
		] );

		\curl_setopt( $this->ch, \CURLOPT_FOLLOWLOCATION, true );
		foreach ( $opts as $key => $value ) {
			\curl_setopt( $this->ch, $key, $value );
		}

		$result = \curl_exec( $this->ch );
		if ( !\is_string( $result ) ) {
			throw new DomainException( \curl_error( $this->ch ) . ': ' . $url );
		}

		return $result;
	}

	/**
	 * Get JSON data structure as PHP object from the CAT API.
	 *
	 * @param string[] $query Parameters for the CAT API, needs at least action
	 * @param string   $lang  Desired language for friendly strings
	 * @param int      $cache Amount of seconds the result is cached, NULL indicates that the global value shoud be used
	 *
	 * @return \stdClass JSON-decoded answer from CAT API
	 */
	private function catJSONQuery( $query, $lang = '', $cache = null ): \stdClass
	{
		$rawResult = $this->executeCatQuery( $query, $lang, 'application/json', $cache );
		$result = \json_decode( $rawResult );
		if ( $result instanceof \stdClass ) {
			return $result;
		}

		throw new DomainException( 'Cannot read CAT answer as JSON dictionary' );
	}

	/**
	 * Get JSON data structure as PHP object from the CAT API.
	 *
	 * @param string[] $query Parameters for the CAT API, needs at least action
	 * @param string   $lang  Desired language for friendly strings
	 * @param int      $cache Amount of seconds the result is cached, NULL indicates that the global value shoud be used
	 *
	 * @return array JSON-decoded answer from CAT API
	 */
	private function catJSONQueryArray( $query, $lang = '', $cache = null ): array
	{
		$rawResult = $this->executeCatQuery( $query, $lang, 'application/json', $cache );
		$result = \json_decode( $rawResult );
		if ( \is_array( $result ) ) {
			return $result;
		}

		throw new DomainException( 'Cannot read CAT answer as JSON array' );
	}

	/**
	 * Get raw answer from CAT API.
	 *
	 * @param string[] $query  Parameters for the CAT API, needs at least action
	 * @param string   $lang   Desired language for friendly strings
	 * @param string   $accept Accepted content type for answer (request is always form-encoded)
	 * @param int      $cache  Amount of seconds the result is cached, NULL indicates that the global value shoud be used
	 *
	 * @return string Raw answer from CAT query
	 */
	private function executeCatQuery( $query, $lang = '', $accept = 'application/json', $cache = null )
	{
		++$this->requestCount;
		if ( !isset( $cache ) ) {
			$cache = $this->cache;
		}
		$file = $this->getCatQueryFilename( $query, $lang, $accept );
		$useLocal = \file_exists( $file ) && \filemtime( $file ) > \time() - $cache;
		$url = $this->getCatURL( $query, $lang );
		if ( $useLocal ) {
			$result = \file_get_contents( $file );
		} else {
			++$this->uncachedRequestCount;
			$result = $this->file_get_contents_curl( $url, $accept );
			\file_put_contents( $file, $result );
		}
		if ( $result ) {
			return $result;
		}
		$this->flushCatQuery( $query, $lang, $accept );
		throw new DomainException( 'Empty result from ' . $url );
	}

	/**
	 * Build the URL used for the given CAT query.
	 *
	 * This function simply concatinates the base URL with a generated
	 * query string from the query argument.
	 *
	 * @param string[] $query Indexed array with query parameters
	 * @param string   $lang  Desired language for friendly strings
	 *
	 * @return string URL for the API endpoint
	 */
	private function getCatURL( $query, $lang = '' )
	{
		if ( $lang ) {
			$query['lang'] = $lang;
		}

		return $this->getBase() . '?' . \http_build_query( $query, '', '&', \PHP_QUERY_RFC3986 );
	}

	/**
	 * Get the filename for a cached CAT API response.
	 *
	 * @param string[] $query  Parameters for the CAT API, needs at least action
	 * @param string   $lang   Desired language for friendly strings
	 * @param string   $accept Accepted content type for answer (request is always form-encoded)
	 *
	 * @return string Full path to the cached CAT API response (may not exist yet)
	 */
	private function getCatQueryFilename( $query, $lang = '', $accept = 'application/json' )
	{
		$hash = \hash( static::CACHE_HASH_FUNCTION, \serialize( $query ) . $this->getBase() . "#${lang}${accept}" );
		$file = \sys_get_temp_dir() . \DIRECTORY_SEPARATOR . 'eduroam-';
		if ( isset( $query['action'] ) ) {
			$file .= $query['action'] . '-';
		}
		if ( isset( $query['federation'] ) ) {
			$file .= $query['federation'] . '-';
		}
		if ( isset( $query['idp'] ) ) {
			$file .= $query['idp'] . '-';
		}
		if ( isset( $query['profile'] ) ) {
			$file .= $query['profile'] . '-';
		}
		if ( isset( $query['device'] ) ) {
			$file .= $query['device'] . '-';
		}
		$file .= $hash;

		return $file;
	}

	/**
	 * Make sure that the answer to the provided query is not cached.
	 *
	 * This is done by removing the cache file.
	 * After this function completes, the next call to #executeCatQuery will
	 * guaranteed get its result from the server.
	 *
	 * @param string[] $query  Parameters for the CAT API, needs at least action
	 * @param string   $lang   Desired language for friendly strings
	 * @param string   $accept Accepted content type for answer (request is always form-encoded)
	 */
	private function flushCatQuery( $query, $lang = '', $accept = 'application/json' ): void
	{
		$file = $this->getCatQueryFilename( $query, $lang, $accept );
		\unlink( $file );
	}
}
