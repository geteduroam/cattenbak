<?php declare(strict_types=1);

/*
 * This file is part of the PHP eduroam CAT client
 * A client to download data from https://cat.eduroam.org/
 *
 * Copyright: 2018-2020, Jørn Åne de Jong, Uninett AS <jorn.dejong@uninett.no>
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

namespace eduroam\CAT;

use stdClass;

/**
 * Configuration profile.
 *
 * An identity provider may have one or more profiles.  These represent a method
 * to configure eduroam and will typically be available for multiple devices.
 */
class Profile
{
	/**
	 * List of all profiles by CAT base, identity provider and language.
	 *
	 * This profile data structure contains the name of the profile.
	 *
	 * This variable is static to facilitate lazy-loading.
	 * The CAT API has no support to get one identity provider,
	 * so we'll have to get them all at the same time.
	 *
	 * @see https://cat.eduroam.org/doc/UserAPI/tutorial_UserAPI.pkg.html#actions.listProfiles
	 */
	public static $profiles;

	/**
	 * List of all profile attributes by CAT base, identity provider and language.
	 *
	 * This profile data structure contains data about the profile, such as
	 * devices, support information and custom texts.
	 *
	 * This variable is static to facilitate lazy-loading.
	 * The CAT API has no support to get one identity provider,
	 * so we'll have to get them all at the same time.
	 *
	 * @see https://cat.eduroam.org/doc/UserAPI/tutorial_UserAPI.pkg.html#actions.listProfiles
	 */
	public static $profileAttributes;

	/**
	 * CAT instance
	 *
	 * @var CAT
	 */
	private $cat;

	/**
	 * Identity provider Entity ID in CAT API
	 *
	 * @var int
	 */
	private $idpID;

	/**
	 * Profile ID in CAT API
	 *
	 * @var int
	 */
	private $profileID;

	/**
	 * Language flag to use in requests against CAT
	 *
	 * @var string
	 */
	private $lang;

	/**
	 * Construct a lazy loaded profile.
	 *
	 * @param CAT    $cat       CAT instance
	 * @param int    $idpID     Identity provider ID
	 * @param int    $profileID Profile ID
	 * @param string $lang      Language
	 */
	public function __construct( CAT $cat, int $idpID, int $profileID, string $lang = '' )
	{
		$this->cat = $cat;
		$this->idpID = $idpID;
		$this->profileID = $profileID;
		$this->lang = $lang;
	}

	/**
	 * Get all profiles as lazy loaded objects in an indexed array.
	 *
	 * @param CAT    $cat   CAT instance
	 * @param int    $idpID Identity provider ID
	 * @param string $lang  Language
	 *
	 * @return Profile[]
	 */
	public static function getProfilesByIdPEntityID( CAT $cat, int $idpID, string $lang = '' ): array
	{
		static::loadProfilesByIdPEntityID( $cat, $idpID, $lang );
		$profiles = [];
		foreach ( static::$profiles[$cat->getBase()][$idpID][$lang] as $profile ) {
			$profiles[$profile->id] = new self( $cat, $idpID, (int)$profile->id, $lang );
		}

		return $profiles;
	}

	/**
	 * Get raw devices by profile ID.
	 *
	 * This method gets the devices from the already loaded profile attributes,
	 * or returns null.  This way, the devices that were sent with the attributes
	 * may be reused instead of retrieving them again.
	 *
	 * @param CAT    $cat       CAT instance
	 * @param int    $profileID Profile ID
	 * @param string $lang      Language
	 *
	 * @return stdClass[]
	 */
	public static function getRawDevicesByProfileID( CAT $cat, int $profileID, string $lang = '' ): array
	{
		$attr = self::loadProfileAttributesByID( $cat, $profileID, $lang );
		if ( isset( $attr->devices ) ) {
			return $attr->devices;
		}

		return [];
	}

	/**
	 * Get the raw data associated with this profile, containing the name.
	 *
	 * This is the JSON data converted to a PHP object.
	 *
	 * @return stdClass
	 */
	public function getRaw(): stdClass
	{
		self::loadProfileAttributesByID( $this->cat, $this->profileID, $this->lang );

		return static::$profileAttributes[$this->cat->getBase()][$this->profileID][$this->lang];
	}

	/**
	 * Get the raw data of this profile's attributes, containing contact info and
	 * devices.
	 *
	 * This is the JSON data converted to a PHP object.
	 *
	 * @return stdClass
	 */
	public function getRawAttributes(): stdClass
	{
		self::loadProfilesByIdPEntityID( $this->cat, $this->idpID, $this->lang );

		return static::$profiles[$this->cat->getBase()][$this->idpID][$this->lang][$this->profileID];
	}

	/**
	 * Get the ID of this profile as it is stored in the CAT database.
	 *
	 * @return int The profile ID
	 */
	public function getProfileID(): int
	{
		return $this->profileID;
	}

	/**
	 * Get the ID of this identity provider as it is stored in the CAT database.
	 *
	 * @return int The identity provider ID
	 */
	public function getIdpID(): int
	{
		return $this->idpID;
	}

	/**
	 * Get the friendly name of this profile.
	 *
	 * @return string The friendly name of this profile
	 */
	public function getDisplay(): string
	{
		static::loadProfilesByIdPEntityID( $this->cat, $this->idpID, $this->lang );
		if ( !static::$profiles[$this->cat->getBase()][$this->idpID][$this->lang][$this->profileID]->display ) {
			return $this->getIdentityProvider()->getDisplay();
		}

		return $this->getRawAttributes()->display;
	}

	/*
	 * omitting #hasLogo() and #getIdentityProviderName() because these
	 * belong in the IdentityProvider class.
	 */

	/**
	 * Get the support e-mail address for this profile.
	 *
	 * @return null|string support e-mail address for this profile
	 */
	public function getLocalEmail()
	{
		$raw = $this->getRaw();
		if ( isset( $raw->local_email ) ) {
			return $raw->local_email;
		}
	}

	/**
	 * Get the support telephone number address for this profile.
	 *
	 * @return null|string support telephone number address for this profile
	 */
	public function getLocalPhone()
	{
		$raw = $this->getRaw();
		if ( isset( $raw->local_phone ) ) {
			return $raw->local_phone;
		}
	}

	/**
	 * Get the support URL address for this profile.
	 *
	 * @return null|string support URL address for this profile
	 */
	public function getLocalUrl()
	{
		$raw = $this->getRaw();
		if ( isset( $raw->local_url ) ) {
			return $raw->local_url;
		}
	}

	/**
	 * Get the description for this profile in plain unformatted text.
	 * This is displayed on the download page.
	 *
	 * @return null|string support e-mail address for this profile
	 */
	public function getDescription()
	{
		$raw = $this->getRaw();
		if ( isset( $raw->description ) ) {
			return $raw->description;
		}
	}

	/**
	 * Get the supported devices for this profile in an indexed array.
	 *
	 * @return Device[]
	 */
	public function getDevices(): array
	{
		static::loadProfileAttributesByID( $this->cat, $this->profileID );
		$devices = [];
		$addPem = false;
		foreach ( $this->getRaw()->devices as $device ) {
			if ( ( $device->redirect || 0 === $device->status ) && ( !isset( $device->options->hidden ) || !$device->options->hidden ) ) {
				$devices[$device->id] = new Device( $this->cat, $this->idpID, $this->profileID, $device->id, $this->lang );
			}
			//$addPem |= !$device->redirect;
			if ( !$device->redirect ) {
				$addPem = true;
			}
		}
		if ( $addPem ) {
			$devices['x-pem'] = new PemDevice( $this->cat, $this->idpID, $this->profileID, 'eap-config', $this->lang );
		}

		return $devices;
	}

	/**
	 * (undocumented feature)
	 *
	 * GÉANT has a service Managed IdP, which had the code name Silver Bullet
	 * It's possible in CAT to make a Managed IdP profile, but this does not show up
	 * in the eap-config file.
	 *
	 * @return bool silverbullet is set and is not intval(0)
	 */
	public function isSilverBullet(): bool
	{
		return isset( $this->getRaw()->silverbullet ) && 0 !== $this->getRaw()->silverbullet;
	}

	public function getDevice( string $deviceID ): Device
	{
		$devices = $this->getDevices();
		if ( \array_key_exists( $deviceID, $devices ) ) {
			return $devices[$deviceID];
		}
		throw new \DomainException( 'Profile ' . $this->getDisplay() . " has no device ${deviceID}" );
	}

	/**
	 * Determines whether this profile is supported by the identity provider.
	 * A profile is considered supported if one of the following is available:
	 * support email, support phone, local url.
	 *
	 * @return bool This profile is supported
	 */
	public function hasSupport(): bool
	{
		return $this->getLocalEmail() || $this->getLocalPhone() || $this->getLocalUrl();
	}

	/**
	 * Get a lazy loaded instance of the identity provider that is associated with
	 * this profile.
	 *
	 * @return IdentityProvider
	 */
	public function getIdentityProvider(): IdentityProvider
	{
		return new IdentityProvider( $this->cat, $this->idpID, $this->lang );
	}

	/**
	 * Determines whether a redirect is set for this profile.
	 *
	 * @return bool Profile has a redirect set
	 */
	public function isRedirect(): bool
	{
		$raw = $this->getRaw();

		// Special case, a redirect-only profile will only have one devices
		// that does not have a name, so the call to getDevices will fail.
		if ( isset( $raw->devices ) && 1 === \count( $raw->devices ) && isset( $raw->devices[0] ) ) {
			if ( isset( $raw->devices[0]->redirect ) ) {
				if ( $raw->devices[0]->redirect ) {
					return true;
				}
			}
		}

		// Return true if every device is a redirect
		foreach ( $this->getDevices() as $device ) {
			if ( !$device->isProfileRedirect() ) {
				return false;
			}
		}

		return true;
	}

	/**
	 * Attempt to get the redirect url for this profile.
	 *
	 * @return ?string The redirect URL
	 */
	public function getRedirectUrl(): ?string
	{
		$raw = $this->getRaw();
		if ( isset( $raw->devices ) && 1 === \count( $raw->devices ) && isset( $raw->devices[0] ) ) {
			if ( isset( $raw->devices[0]->redirect ) ) {
				if ( $raw->devices[0]->redirect ) {
					return $raw->devices[0]->redirect;
				}
			}
		}

		return null;
	}

	/**
	 * Fill lazy loaded $profiles.
	 *
	 * @param CAT    $cat   CAT instance
	 * @param int    $idpID Identity provider ID
	 * @param string $lang  Language
	 */
	private static function loadProfilesByIdPEntityID( CAT $cat, int $idpID, string $lang = '' ): void
	{
		if ( !isset( static::$profiles[$cat->getBase()][$idpID][$lang] ) ) {
			foreach ( $cat->listProfiles( $idpID, $lang ) as $profile ) {
				static::$profiles[$cat->getBase()][$idpID][$lang][$profile->id] = $profile;
			}
		}
	}

	/**
	 * Fill lazy loaded profile with its attributes.
	 *
	 * @param CAT    $cat       CAT instance
	 * @param int    $profileID Profile ID
	 * @param string $lang      Language
	 */
	private static function loadProfileAttributesByID( CAT $cat, int $profileID, string $lang = '' ): stdClass
	{
		if ( !isset( static::$profileAttributes[$cat->getBase()][$profileID][$lang] ) ) {
			static::$profileAttributes[$cat->getBase()][$profileID][$lang] = $cat->profileAttributes( $profileID, $lang );
		}
		if ( !isset( static::$profileAttributes[$cat->getBase()][$profileID][$lang] ) ) {
			throw new \DomainException( 'Unable to load profile attributes for profile ' . $profileID );
		}

		return static::$profileAttributes[$cat->getBase()][$profileID][$lang];
	}
}
