;; What follows is a "manifest" equivalent to the command line you gave.
;; You can store it in a file that you may then pass to any 'guix' command
;; that accepts a '--manifest' (or '-m') option.

(load "trueskill.scm")

(packages->manifest (cons* python-trueskill
						   (specifications->packages
							(list "python"
								  "python-pandas"
								  "python-odfpy"
								  "python-matplotlib"
								  "python-colorama"
								  "python-mpmath"))))
