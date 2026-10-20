"""
ChampSim compilation builder.
Builds ChampSim binaries with explicit cache geometries and component configurations
without mutating headers on disk.
"""

import os
import shutil
import subprocess
from typing import Optional
from framework.geometry import CacheGeometry


class BuildError(Exception):
    """Raised when compilation fails."""
    pass


class ChampSimBuilder:
    def __init__(self, workspace_root: str):
        self.root = os.path.abspath(workspace_root)
        self.bin_dir = os.path.join(self.root, "bin")
        os.makedirs(self.bin_dir, exist_ok=True)

    def get_binary_name(
        self,
        branch: str,
        llc_repl: str,
        geometry: CacheGeometry,
        cores: int = 1,
        l1i_pref: str = "no",
        l1d_pref: str = "no",
        l2c_pref: str = "no",
        llc_pref: str = "no",
    ) -> str:
        """Construct an unambiguous binary name containing all configuration parameters."""
        cap_str = f"{geometry.capacity_mb:g}MB"
        return (
            f"champsim_{branch}_{llc_repl}_{cap_str}_{geometry.ways}way_{cores}core"
        )

    def build(
        self,
        branch: str,
        llc_repl: str,
        geometry: CacheGeometry,
        cores: int = 1,
        l1i_pref: str = "no",
        l1d_pref: str = "no",
        l2c_pref: str = "no",
        llc_pref: str = "no",
        force_rebuild: bool = False,
    ) -> str:
        """
        Builds the simulator with the specified configuration.
        Returns the absolute path to the compiled binary.
        """
        binary_name = self.get_binary_name(
            branch=branch,
            llc_repl=llc_repl,
            geometry=geometry,
            cores=cores,
            l1i_pref=l1i_pref,
            l1d_pref=l1d_pref,
            l2c_pref=l2c_pref,
            llc_pref=llc_pref,
        )
        target_bin = os.path.join(self.bin_dir, binary_name)

        if os.path.exists(target_bin) and not force_rebuild:
            return target_bin

        # Source files validation
        branch_src = os.path.join(self.root, "branch", f"{branch}.bpred")
        repl_src = os.path.join(self.root, "replacement", f"{llc_repl}.llc_repl")
        if not os.path.exists(branch_src):
            raise BuildError(f"Branch predictor source not found: {branch_src}")
        if not os.path.exists(repl_src):
            raise BuildError(f"LLC replacement source not found: {repl_src}")

        # Copy component files into place
        shutil.copy(branch_src, os.path.join(self.root, "branch", "branch_predictor.cc"))
        shutil.copy(repl_src, os.path.join(self.root, "replacement", "llc_replacement.cc"))
        shutil.copy(
            os.path.join(self.root, "prefetcher", f"{l1i_pref}.l1i_pref"),
            os.path.join(self.root, "prefetcher", "l1i_prefetcher.cc")
        )
        shutil.copy(
            os.path.join(self.root, "prefetcher", f"{l1d_pref}.l1d_pref"),
            os.path.join(self.root, "prefetcher", "l1d_prefetcher.cc")
        )
        shutil.copy(
            os.path.join(self.root, "prefetcher", f"{l2c_pref}.l2c_pref"),
            os.path.join(self.root, "prefetcher", "l2c_prefetcher.cc")
        )
        shutil.copy(
            os.path.join(self.root, "prefetcher", f"{llc_pref}.llc_pref"),
            os.path.join(self.root, "prefetcher", "llc_prefetcher.cc")
        )

        # Prepare compiler flags
        # Extra flags for cache geometry
        extra_cflags = geometry.get_cflags()
        if cores > 1:
            extra_cflags += f" -DNUM_CPUS={cores}"

        # Clean old object files to prevent ODR violations
        clean_res = subprocess.run(
            ["make", "clean"],
            cwd=self.root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if clean_res.returncode != 0:
            raise BuildError(f"make clean failed: {clean_res.stderr}")

        # Run make
        cmd = ["make", "-j4", f"EXTRA_CFLAGS={extra_cflags}"]
        build_res = subprocess.run(
            cmd,
            cwd=self.root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if build_res.returncode != 0:
            raise BuildError(f"Compilation failed:\n{build_res.stderr}\n{build_res.stdout}")

        built_bin = os.path.join(self.bin_dir, "champsim")
        if not os.path.exists(built_bin):
            raise BuildError(f"Target binary not generated: {built_bin}")

        # Rename to unique binary
        shutil.move(built_bin, target_bin)
        return target_bin
