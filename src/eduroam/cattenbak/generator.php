<?php declare(strict_types=1);

/*
 * This file is part of the Cattenbak
 * The discovery file generator for geteduroam
 *
 * Copyright: 2020, Jørn Åne de Jong, Uninett AS <jorn.dejong@uninett.no>
 * SPDX-License-Identifier: BSD-3-Clause
 */

namespace eduroam\Cattenbak;

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
		return \json_encode( $data, \JSON_PRETTY_PRINT | \JSON_UNESCAPED_SLASHES | \JSON_UNESCAPED_UNICODE ) . "\n";
	}

	protected function writeFile( string $file, string $contents ): void
	{
		if ( !\file_put_contents( $file, $contents ) ) {
			throw new \RuntimeException( "Unable to write file ${file}" );
		}
	}
}
