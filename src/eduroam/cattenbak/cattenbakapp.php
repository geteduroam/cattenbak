<?php declare(strict_types=1);

/*
 * This file is part of the Cattenbak
 * The discovery file generator for geteduroam
 *
 * Copyright: 2020, Jørn Åne de Jong, Uninett AS <jorn.dejong@uninett.no>
 * SPDX-License-Identifier: BSD-3-Clause
 */

namespace eduroam\Cattenbak;

use eduroam\CAT\CAT;
use RuntimeException;

class CattenbakApp
{
	/** @var array */
	private $config;

	/** @var ?CAT */
	private $cat = null;

	/** @var ?int */
	private $seq;

	/** @var ?resource */
	private $handle;

	/**
	 * Instantiate app
	 *
	 * @param array|?string $config Configuration array or location of config file
	 * @psalm-suppress UnresolvableInclude
	 */
	public function __construct( $config = null )
	{
		if ( \is_array( $config ) ) {
			$this->config = $config;
		} elseif ( \is_string( $config ) ) {
			$this->config = require $config;
		} else {
			$this->config = require \dirname( __DIR__, 3 ) . '/etc/cattenbak.conf.php';
		}
	}

	/**
	 * @return CAT
	 */
	public function getCAT(): CAT
	{
		if ( null === $this->cat ) {
			if ( \array_key_exists( 'cat', $this->config ) ) {
				if ( $this->config['cat'] instanceof CAT ) {
					$this->cat = $this->config['cat'];
				} else {
					throw new \DomainException( 'Configuration contains custom cat, but it is not a CAT object' );
				}
			} else {
				if ( \array_key_exists( 'cacheTime', $this->config ) ) {
					if ( !\is_int( $this->config['cacheTime'] ) ) {
						throw new \DomainException( 'cacheTime must be integer if set' );
					}
				}
				$this->cat = new CAT( 'https://cat.eduroam.org/user/API.php', $this->getOptionalInt( 'cacheTime' ) ?? 604800 );
			}
		}

		return $this->cat;
	}

	/**
	 * @return int
	 */
	public function getSeq(): int
	{
		if ( null !== $this->seq ) {
			return $this->seq;
		}
		$file = \dirname( __DIR__, 3 ) . \DIRECTORY_SEPARATOR . 'serial.txt';
		$handle = \fopen( $file, 'c+' );
		if ( false === $handle ) {
			throw new RuntimeException( 'Unable to open serial.txt' );
		}
		if ( !\flock( $handle, \LOCK_EX ) ) {
			throw new RuntimeException( 'Unable to lock serial.txt' );
		}
		$this->handle = $handle;
		$seq = \fread( $this->handle, 100 );
		if ( false === $seq ) {
			throw new RuntimeException( 'Unable to read serial.txt' );
		}
		$seq = \trim( $seq );
		if ( !\is_numeric( $seq ) || (int)$seq <= 0 ) {
			throw new RuntimeException( 'serial.txt contains a negative or invalid number, must be positive' );
		}
		$this->seq = (int)$seq + 1;

		return $this->seq;
	}

	public function incrSeq(): void
	{
		$seq = $this->getSeq();
		\assert( null !== $this->handle, 'handle is null after calling getSeq' );
		\rewind( $this->handle );
		\fwrite( $this->handle, $seq . "\n" );
		\flock( $this->handle, \LOCK_UN );
	}

	/**
	 * @return int[]
	 */
	public function getHiddenInstitutions(): array
	{
		return $this->getOptionalArray( 'hiddenInstitutes' ) ?? [];
	}

	/**
	 * @return int[]
	 */
	public function getHiddenProfiles(): array
	{
		return $this->getOptionalArray( 'hiddenProfiles' ) ?? [];
	}

	/**
	 * @return string[]
	 */
	public function getCountries(): array
	{
		return  $this->getArray( 'countries' );
	}

	/**
	 * @return array[]
	 */
	public function getGetEduroamProfiles(): array
	{
		return $this->getOptionalArray( 'getEduroamProfiles' ) ?? [];
	}

	/**
	 * @return array[]
	 */
	public function getGetExtraIdps(): array
	{
		return $this->getOptionalArray( 'extraIdps' ) ?? [];
	}

	protected function getOptionalInt( string $key ): ?int
	{
		if ( !\array_key_exists( $key, $this->config ) ) {
			return null;
		}
		// Phan doesn't trust $this->config not to change on the next three lines
		$result = $this->config[$key];
		if ( \is_int( $result ) ) {
			return $result;
		}
		throw new \DomainException( "Configuration setting ${key} must be integer if set" );
	}

	protected function getInt( string $key ): int
	{
		$result = $this->getOptionalInt( $key );
		if ( null === $result ) {
			throw new \DomainException( "Configuration setting ${key} must be set" );
		}

		return $result;
	}

	protected function getOptionalArray( string $key ): ?array
	{
		if ( !\array_key_exists( $key, $this->config ) ) {
			return null;
		}
		// Phan doesn't trust $this->config not to change on the next three lines
		$result = $this->config[$key];
		if ( \is_array( $result ) ) {
			return $result;
		}
		throw new \DomainException( "Configuration setting ${key} must be array if set" );
	}

	protected function getArray( string $key ): array
	{
		$result = $this->getOptionalArray( $key );
		if ( null === $result ) {
			throw new \DomainException( "Configuration setting ${key} must be set" );
		}

		return $result;
	}
}
