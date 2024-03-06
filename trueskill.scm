(use-modules
	(guix packages)
	(guix build-system python)
	(guix build-system pyproject)
	(guix download)
	((guix licenses) #:prefix license:)
	(gnu packages python-xyz))


(define-public python-trueskill
  (package
    (name "python-trueskill")
    (version "0.4.5")
    (source
     (origin
       (method url-fetch)
       (uri (pypi-uri "trueskill" version))
       (sha256
        (base32 "1fv7g1szyjykja9mzax2w4js7jm2z7wwzgnr5dqrsdi84j6v8qlx"))))
    (arguments
     `(#:phases
       (modify-phases %standard-phases
	(delete 'check))))
    (build-system pyproject-build-system)
    (propagated-inputs (list python-six))
    (home-page "http://trueskill.org/")
    (synopsis "The video game rating system")
    (description "The video game rating system")
    (license license:bsd-3)))


python-trueskill
