<?php declare(strict_types=1);

/*
 * This file is part of the Cattenbak
 * The discovery file generator for geteduroam
 *
 * Copyright: 2020, Jørn Åne de Jong, Uninett AS <jorn.dejong@uninett.no>
 * SPDX-License-Identifier: BSD-3-Clause
 */

namespace eduroam\Cattenbak;

use eduroam\CAT\IdentityProvider;
use eduroam\CAT\Profile;

class V1Generator extends Generator
{
	public function generate(): array
	{
		$instances = $this->getApp()->getGetExtraIdps();
		foreach ( $this->getIdpsForCountries() as $idp ) {
			if ( \in_array( $idp->getEntityID(), $this->getApp()->getHiddenInstitutions(), true ) ) {
				continue;
			}
			$profiles = $this->fetchProfileDataForIdP( $idp );
			if ( \count( $profiles ) > 0 ) {
				$instances[] = $this->getIdPData( $idp ) + ['profiles' => $profiles];
			}
		}
		\usort($instances, [$this, 'idpSorter']);

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

	protected function getIdpsForCountries( ?array $countries = null ): array
	{
		if ( null === $countries) {
			$countries = $this->getApp()->getCountries();
		}
		$idps = [];
		foreach ( $countries as $country ) {
			$idps += IdentityProvider::getIdentityProvidersByCountry( $this->getApp()->getCAT(), $country );
		}

		return $idps;
	}

	protected static function getProfileData( Profile $profile ): array
	{
		return [
			'id' => 'cat_' . $profile->getProfileID(),
			'cat_profile' => $profile->getProfileID(),
			'name' => $profile->getDisplay(),
			'eapconfig_endpoint' => $profile->getDevice( 'eap-config' )->getDownloadLink(),
			'oauth' => false,
		];
	}

	protected static function getIdPData( IdentityProvider $idp): array
	{
		return [
			'name' => $idp->getTitle(),
			'country' => $idp->getCountry(),
			'cat_idp' => $idp->getEntityID(),
		];
	}

	protected function fetchProfileDataForIdP( IdentityProvider $idp ): array
	{
		$geProfiles = $this->getApp()->getGetEduroamProfiles();
		$profiles = \array_key_exists( $idp->getEntityID(), $geProfiles )
			? $geProfiles[$idp->getEntityID()]
			: []
			;
		foreach ( $idp->getProfiles() as $profile ) {
			if ( \in_array( $profile->getProfileID(), $this->getApp()->getHiddenProfiles(), true ) || $profile->isSilverBullet() || $profile->isRedirect() ) {
				continue;
			}
			$profiles[] = $this->getProfileData( $profile );
		}

		return $profiles;
	}

	protected function writeFiles( string $dir ): void
	{
		$seq = $this->getApp()->getSeq();
		$this->writeFile( "${dir}/discovery-${seq}.json", $this->jsonEncode( $this->generate() ) );
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
