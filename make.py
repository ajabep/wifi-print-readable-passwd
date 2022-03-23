"""
Steal django code to generate translations and compile them!
"""
import glob
import os
import re

import click
from django.core.files.temp import NamedTemporaryFile
from django.core.management.base import CommandError
from django.core.management.commands.compilemessages import Command as DjangoCompileCommand
from django.core.management.commands.makemessages import Command as DjangoCollectCommand
from django.core.management.commands.makemessages import check_programs, STATUS_OK, NO_LOCALE_DIR, write_pot_file
from django.core.management.utils import (
    handle_extensions,
)
from django.core.management.utils import (
    popen_wrapper,
)
from django.utils.text import get_text_list


class CollectCommand(DjangoCollectCommand):
    # noinspection PyAttributeOutsideInit
    def handle(self, *args, **options):
        locale = options["locale"]
        self.domain = options["domain"]

        self.verbosity = options["verbosity"]
        self.symlinks = options["symlinks"]
        self.no_obsolete = options["no_obsolete"]

        ignore_patterns = options["ignore_patterns"]
        ignore_patterns += ["CVS", ".*", "*~", "*.pyc"]
        self.ignore_patterns = list(set(ignore_patterns))

        exts = ["html", "txt", "py"]
        self.extensions = handle_extensions(exts)

        if self.verbosity > 1:
            self.stdout.write(
                "examining files with the extensions: %s"
                % get_text_list(list(self.extensions), "and")
            )

        self.invoked_for_django = False
        self.locale_paths = []
        self.locale_paths.append(os.path.abspath("locale"))
        self.default_locale_path = self.locale_paths[0]
        os.makedirs(self.default_locale_path, exist_ok=True)

        # Build locale list
        looks_like_locale = re.compile(r"[a-z]{2}")
        locale_dirs = filter(
            os.path.isdir, glob.glob("%s/*" % self.default_locale_path)
        )
        all_locales = [
            lang_code
            for lang_code in map(os.path.basename, locale_dirs)
            if looks_like_locale.match(lang_code)
        ]

        locales = locale or all_locales

        if locales:
            check_programs("msguniq", "msgmerge", "msgattrib")

        check_programs("xgettext")

        try:
            potfiles = self.build_potfiles()

            # Build po files for each selected locale
            for locale in locales:
                if "-" in locale:
                    self.stdout.write(
                        "invalid locale %s, did you mean %s?"
                        % (
                            locale,
                            locale.replace("-", "_"),
                        ),
                    )
                    continue
                if self.verbosity > 0:
                    self.stdout.write("processing locale %s" % locale)
                for potfile in potfiles:
                    self.write_po_file(potfile, locale)
        finally:
            self.remove_potfiles()

    def process_locale_dir(self, locale_dir, files):
        """
        Extract translatable literals from the specified files, creating or
        updating the POT file for a given locale directory.

        Use the xgettext GNU gettext utility.
        """
        build_files = []
        for translatable in files:
            if self.verbosity > 1:
                self.stdout.write(
                    "processing file %s in %s"
                    % (translatable.file, translatable.dirpath)
                )
            build_file = self.build_file_class(self, self.domain, translatable)
            try:
                build_file.preprocess()
            except UnicodeDecodeError as e:
                self.stdout.write(
                    "UnicodeDecodeError: skipped file %s in %s (reason: %s)"
                    % (
                        translatable.file,
                        translatable.dirpath,
                        e,
                    )
                )
                continue
            except BaseException:
                # Cleanup before exit.
                for build_file in build_files:
                    build_file.cleanup()
                raise
            build_files.append(build_file)

        args = [
            "xgettext",
            "-d",
            self.domain,
            "--language=Python",
            "--keyword=gettext_noop",
            "--keyword=gettext_lazy",
            "--keyword=ngettext_lazy:1,2",
            "--keyword=pgettext:1c,2",
            "--keyword=npgettext:1c,2,3",
            "--keyword=pgettext_lazy:1c,2",
            "--keyword=npgettext_lazy:1c,2,3",
            "--output=-",
        ]

        input_files = [bf.work_path for bf in build_files]
        with NamedTemporaryFile(mode="w+") as input_files_list:
            input_files_list.write("\n".join(input_files))
            input_files_list.flush()
            args.extend(["--files-from", input_files_list.name])
            args.extend(self.xgettext_options)
            msgs, errors, status = popen_wrapper(args)

        if errors:
            if status != STATUS_OK:
                for build_file in build_files:
                    build_file.cleanup()
                raise CommandError(
                    "errors happened while running xgettext on %s\n%s"
                    % ("\n".join(input_files), errors)
                )
            elif self.verbosity > 0:
                # Print warnings
                self.stdout.write(errors)

        if msgs:
            if locale_dir is NO_LOCALE_DIR:
                for build_file in build_files:
                    build_file.cleanup()
                file_path = os.path.normpath(build_files[0].path)
                raise CommandError(
                    "Unable to find a locale path to store translations for "
                    "file %s. Make sure the 'locale' directory exists in an "
                    "app or LOCALE_PATHS setting is set." % file_path
                )
            for build_file in build_files:
                msgs = build_file.postprocess_messages(msgs)
            potfile = os.path.join(locale_dir, "%s.pot" % self.domain)
            write_pot_file(potfile, msgs)

        for build_file in build_files:
            build_file.cleanup()


@click.group()
def main():
    pass


@main.command()
@click.option('-l', multiple=True, type=str, help='Creates or updates the message files for the given locale(s) (e.g. '
                                                  'pt_BR). Can be used multiple times. ')
def collect(**options):
    args = [
        '-l=' + lang
        for lang in options['l']
    ]
    args.extend([
        '--ignore=fonts',
        '--domain=locale'
    ])
    c = CollectCommand()
    parser = c.create_parser("", "")

    # noinspection PyProtectedMember
    kwargs = dict(parser.parse_args(args)._get_kwargs())

    c.handle(**kwargs)


# noinspection PyShadowingBuiltins
@main.command()
def compile():
    args = [
        '--ignore=fonts',
    ]
    c = DjangoCompileCommand()
    parser = c.create_parser("", "")

    # noinspection PyProtectedMember
    kwargs = dict(parser.parse_args(args)._get_kwargs())

    c.handle(**kwargs)


if __name__ == '__main__':
    main()
