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
			$instances[] = $this->getIdPData( $idp ) + ['profiles' => $profiles];
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
		return (int)( $a['cat_idp'] ) - (int)( $b['cat_idp'] );
	}
}
