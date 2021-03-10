<?php declare(strict_types=1);

/*
 * This file is part of the Cattenbak
 * The discovery file generator for geteduroam
 *
 * Copyright: 2020, Jørn Åne de Jong, Uninett AS <jorn.dejong@uninett.no>
 * SPDX-License-Identifier: BSD-3-Clause
 */

namespace eduroam\Cattenbak;

use DomainException;

use eduroam\CAT\IdentityProvider;
use eduroam\CAT\Profile;

use Exception;

class V1Generator extends Generator
{
	public function generate(): array
	{
		$instances = $this->getApp()->getGetExtraIdps();
		foreach ( $this->getIdpsForCountries( $this->getApp()->getCountries() ) as $idp ) {
			if ( \in_array( $idp->getEntityID(), $this->getApp()->getHiddenInstitutions(), true ) ) {
				continue;
			}
			$profiles = $this->fetchProfileDataForIdP( $idp );
			if ( \count( $profiles ) > 0 ) {
				$instances[] = $this->getIdPData( $idp ) + ['profiles' => $profiles];
			}
		}
		\usort( $instances, [$this, 'idpSorter'] );

		return [
			'version' => 1,
			'seq' => $this->getApp()->getSeq(),
			'instances' => $instances,
		];
	}

	public function getVersion(): int
	{
		return 1;
	}

	public function diff( string $dir, int $oldSeq, int $newSeq ): bool
	{
		try {
			$oldPayload = $this->readFile( "${dir}/discovery-${oldSeq}.json" );
		} catch ( \RuntimeException $_ ) {
			$oldPayload = '{}';
		}
		$oldData = \json_decode( $oldPayload, true );
		$newData = \json_decode( $this->readFile( "${dir}/discovery-${newSeq}.json" ), true );
		if ( !\is_array( $oldData ) || !\is_array( $newData ) ) {
			return true;
		}
		unset( $oldData['seq'] , $newData['seq'] );

		return $this->arrayDiff( $oldData, $newData );
	}

	protected function getIdpsForCountries( ?array $countries = null ): array
	{
		if ( empty( $countries ) ) {
			$countries = \array_map(
					static function ($c) {
						return $c->federation;
					}, $this->getApp()->getCAT()->listCountries()
				);
		}
		$idps = [];
		foreach ( $countries as $country ) {
			$idps += IdentityProvider::getIdentityProvidersByCountry( $this->getApp()->getCAT(), $country );
		}

		return $idps;
	}

	protected function getCatProfileData( Profile $profile ): array
	{
		$device = null;
		try {
			$device = $profile->getDevice( 'eap-config' );
		} catch ( Exception $_ ) {
		}
		if ( null === $device || $device->isRedirect() ) {
			// The eap-config device is set to be a redirect
			// We can't reliably determine which URL the user should be redirected to;
			// maybe some device profiles are actually available
			// So we override the redirect URL to be the CAT download page
			$base = $this->getApp()->getCAT()->getBase();
			if ( !\preg_match( '_(([^/]*/){3})_', $base, $match ) ) {
				throw new DomainException( 'CAT base is not a valid URL' );
			}
			$base = $match[0];

			return [
				'id' => 'cat_' . $profile->getProfileID(),
				'redirect' => $base . '?' . \http_build_query( [
					'idp' => $profile->getIdentityProvider()->getEntityID(),
					'profile' => $profile->getProfileID(),
				] ),
				'name' => $profile->getDisplay(),
			];
		}

		$link = $device->getDownloadLink();
		$catnip = $this->getApp()->getCatnip();
		if ( null !== $catnip ) {
			$cat = $this->getApp()->getCAT();
			$link = \str_replace( $cat->getBase(), $catnip, $link );
		}

		return [
			'id' => 'cat_' . $profile->getProfileID(),
			'cat_profile' => $profile->getProfileID(),
			'name' => $profile->getDisplay(),
			'eapconfig_endpoint' => $link,
			'oauth' => false,
		];
	}

	protected static function getLetsWifiProfileData( Profile $profile, int $letswifiCount ): array
	{
		if ( $url = $profile->getRedirectUrl() ) {
			$data = \parse_url( $url );
			if ( false === $data ) {
				// TODO This could be a warning..?
				throw new DomainException( "Illegal redirect URL ${url} for profile {$profile->getProfileID()}" );
			}
			if ( false
				|| !\array_key_exists( 'scheme', $data )
				|| 'https' !== $data['scheme']
				|| !\array_key_exists( 'host', $data )
				|| \array_key_exists( 'port', $data )
				|| \array_key_exists( 'user', $data )
				|| \array_key_exists( 'password', $data )
				|| ( \array_key_exists( 'path', $data ) && '/' !== $data['path'] )
				|| !\array_key_exists( 'fragment', $data )
				|| !\in_array( 'letswifi', \explode( '#', $data['fragment'] ), true )
			) {
				return [
					'id' => 'cat_' . $profile->getProfileID(),
					'redirect' => $url,
					'name' => $profile->getDisplay(),
				];
			}
			$host = $data['host'];
			$query = \array_key_exists( 'query', $data )
				? '?' . $data['query']
				: ''
				;
			$get = [];
			\parse_str( $data['query'] ?? '', $get );

			return [
				'id' => 'letswifi_' . \strtr( $get['realm'] ?? $data['host'], '.', '_' ) . '_cat_' . $profile->getProfileID(),
				'name' => $profile->getDisplay(),
				'default' => 1 === $letswifiCount,
				'eapconfig_endpoint' => "https://${host}/api/eap-config/${query}",
				'token_endpoint' => "https://${host}/oauth/token/${query}",
				'authorization_endpoint' => "https://${host}/oauth/authorize/${query}",
				'oauth' => true,
			];
		}

		return [];
	}

	protected static function getIdPData( IdentityProvider $idp ): array
	{
		return [
			'name' => $idp->getTitle(),
			'country' => $idp->getCountry(),
			'cat_idp' => $idp->getEntityID(),
			'geo' => $idp->getGeo( 3 ), /* round by 3 digits, see xkcd#2170 */
		];
	}

	protected function fetchProfileDataForIdP( IdentityProvider $idp ): array
	{
		$letswifiCount = 0;
		$geProfiles = $this->getApp()->getGetEduroamProfiles();
		$profiles = \array_key_exists( $idp->getEntityID(), $geProfiles )
			? $geProfiles[$idp->getEntityID()]
			: []
			;
		foreach ( $idp->getProfiles() as $profile ) {
			if ( \in_array( $profile->getProfileID(), $this->getApp()->getHiddenProfiles(), true ) || $profile->isSilverBullet() ) {
				continue;
			}
			if ( $profile->isRedirect() ) {
				++$letswifiCount;
				$profileData = $this->getLetsWifiProfileData( $profile, $letswifiCount );
				if ( $profileData ) {
					$profiles[] = $profileData;
				}
			} else {
				$profiles[] = $this->getCatProfileData( $profile );
			}
		}

		return $profiles;
	}

	protected function writeFiles( string $dir ): void
	{
		$seq = $this->getApp()->getSeq();
		$json = $this->jsonEncode( $this->generate() );
		$gzip = $this->gzCompress( $json );
		$this->writeFile( "${dir}/discovery-${seq}.json", $json );
		if ( null !== $gzip ) {
			$this->writeFile( "${dir}/discovery-${seq}.json.gz", $gzip );
		}
	}

	private function idpSorter( array $a, array $b ): int
	{
		// We take the first byte of every string, and check if it is in a-z (insensitive)
		// This allows us to place a lot of institutions that start with a number at the end of the list.
		// In ASCII, numbers come before letters, so otherwise they would have been placed at the start
		//
		// We don't need to take UTF-8 into account here, we just see names that start with UTF-8
		// as non-letters, so they are also placed at the end of the list
		// UTF-8 special characters will always have their first byte outside the a-z range,
		// so that's all we have to check for.
		$modifier = 0;
		$oa = \ord( \substr( $a['name'], 0, 1 ) ) & 0x5f;
		$ob = \ord( \substr( $b['name'], 0, 1 ) ) & 0x5f;
		if ( $oa < 0x41 || $oa > 0x5a ) {
			$modifier += 255;
		}
		if ( $ob < 0x41 || $ob > 0x5a ) {
			$modifier -= 255;
		}

		return \strcasecmp( $a['name'], $b['name'] ) + $modifier;
	}
}
