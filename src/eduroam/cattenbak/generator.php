<?php declare(strict_types=1);

/*
 * This file is part of the Cattenbak
 * The discovery file generator for geteduroam
 *
 * Copyright: 2020, Jørn Åne de Jong, Uninett AS <jorn.dejong@uninett.no>
 * SPDX-License-Identifier: BSD-3-Clause
 */

namespace eduroam\Cattenbak;

use RuntimeException;

abstract class Generator
{
	/** @var CattenbakApp */
	private $app;

	/** @var string */
	private $baseDir;

	public function __construct( CattenbakApp $app, string $baseDir = null )
	{
		$this->app = $app;
		$this->baseDir = $baseDir ?? \dirname( __DIR__, 3 );
	}

	public function write( string $dir = null ): void
	{
		$baseDir = $this->baseDir;
		$ver = 'v' . $this->getVersion();
		if ( null === $dir ) {
			$dir = "${baseDir}/disco/${ver}";
		}

		if ( !\is_dir( $dir ) ) {
			if ( !\mkdir( $dir, 0755, true ) ) {
				throw new \RuntimeException( "Cannot make directory ${dir}" );
			}
		}
		$this->writeFiles( $dir );
		// Bump serial.txt one version up
		$this->getApp()->incrSeq();
	}

	abstract public function generate(): array;

	abstract public function getVersion(): int;

	abstract protected function writeFiles( string $dir ): void;

	protected function getApp(): CattenbakApp
	{
		return $this->app;
	}

	/**
	 * @param array|\stdClass|string $data
	 */
	protected static function jsonEncode( $data ): string
	{
		// I would have added JSON_UNESCAPED_UNICODE as well,
		// but this raised the size of the gzip compressed file
		$result = \json_encode( $data, \JSON_UNESCAPED_SLASHES );
		if ( false === $result ) {
			throw new RuntimeException( 'Unable to serialize data to JSON' );
		}

		return $result;
	}

	protected static function gzCompress( string $data ): ?string
	{
		return \gzencode( $data, 9, \FORCE_GZIP ) ?: null;
	}

	protected function writeFile( string $file, string $contents ): void
	{
		if ( !\file_put_contents( $file, $contents ) ) {
			throw new \RuntimeException( "Unable to write file ${file}" );
		}
	}
}
