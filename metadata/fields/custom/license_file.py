#!/usr/bin/env python3
# Copyright 2023 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import re
import sys
from typing import Union

_THIS_DIR = os.path.abspath(os.path.dirname(__file__))
# The repo's root directory.
_ROOT_DIR = os.path.abspath(os.path.join(_THIS_DIR, "..", "..", ".."))

# Add the repo's root directory for clearer imports.
sys.path.insert(0, _ROOT_DIR)

import metadata.fields.field_types as field_types
import metadata.fields.util as util
import metadata.validation_result as vr

# Pattern for backward directory navigation in paths.
_PATTERN_PATH_BACKWARD = re.compile(r"\.\.\/")

# Deprecated special value for packages that aren't shipped.
_NOT_SHIPPED = "NOT_SHIPPED"


class LicenseFileField(field_types.MetadataField):
  """Custom field for the paths to the package's license file(s)."""
  def __init__(self):
    super().__init__(name="License File", one_liner=True)

  def validate(self, value: str) -> Union[vr.ValidationResult, None]:
    """Checks the given value consists of non-empty paths with no backward
    directory navigation (i.e. no "../").

    This validation is rudimentary. To check if the license file(s) exist on
    disk, see the `LicenseFileField.validate_on_disk` method.

    Note: this field supports multiple values.
    """
    if value == _NOT_SHIPPED:
      return vr.ValidationWarning(
          f"{self._name} uses deprecated value '{_NOT_SHIPPED}'.")

    invalid_values = []
    for path in value.split(self.VALUE_DELIMITER):
      path = path.strip()
      if util.is_empty(path) or util.matches(_PATTERN_PATH_BACKWARD, path):
        invalid_values.append(path)

    if invalid_values:
      template = ("{field_name} has invalid values. Paths cannot be empty, "
                  "or include '../'. If there are multiple license files, "
                  "separate them with a '{delim}'. Invalid values: {values}.")
      message = template.format(field_name=self._name,
                                delim=self.VALUE_DELIMITER,
                                values=util.quoted(invalid_values))
      return vr.ValidationError(message)

    return None

  def validate_on_disk(
      self,
      value: str,
      source_file_dir: str,
      repo_root_dir: str,
  ) -> Union[vr.ValidationResult, None]:
    """Checks the given value consists of file paths which exist on disk.

    Note: this field supports multiple values.

    Args:
      value: the value to validate.
      source_file_dir: the directory of the metadata file that the license file
                       value is from; this is needed to construct file paths to
                       license files.
      repo_root_dir: the repository's root directory; this is needed to
                     construct file paths to license files.

    Returns: a validation result based on the license file value, and whether
             the license file(s) exist on disk, otherwise None.
    """
    if value == _NOT_SHIPPED:
      return vr.ValidationWarning(
          f"{self._name} uses deprecated value '{_NOT_SHIPPED}'.")

    invalid_values = []
    for license_filename in value.split(self.VALUE_DELIMITER):
      license_filename = license_filename.strip()
      if license_filename.startswith("/"):
        license_filepath = os.path.join(
            repo_root_dir, os.path.normpath(license_filename.lstrip("/")))
      else:
        license_filepath = os.path.join(source_file_dir,
                                        os.path.normpath(license_filename))

      if not os.path.exists(license_filepath):
        invalid_values.append(license_filepath)

    if invalid_values:
      template = ("{field_name} has invalid values. Failed to find file(s) on"
                  "local disk. Invalid values: {values}.")
      message = template.format(field_name=self._name,
                                values=util.quoted(invalid_values))
      return vr.ValidationError(message)

    return None
