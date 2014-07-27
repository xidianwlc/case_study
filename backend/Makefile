all:
	[ -d output ] || mkdir output
	find conf  -print | grep -v ".git" | xargs -n 1 echo | cpio -p -d --quiet output/
	find handler -print | grep -v ".git" | xargs -n 1 echo | cpio -p -d --quiet output/
	find model  -print | grep -v ".git" | xargs -n 1 echo | cpio -p -d --quiet output/
	find lib  -print | grep -v ".git" | xargs -n 1 echo | cpio -p -d --quiet output/
	find service  -print | grep -v ".git" | xargs -n 1 echo | cpio -p -d --quiet output/
	find static  -print | grep -v ".git" | xargs -n 1 echo | cpio -p -d --quiet output/
	find tpl  -print | grep -v ".git" | xargs -n 1 echo | cpio -p -d --quiet output/
	cp init.py output/
	if [ -d METAINFO ];then cp -r METAINFO output; fi

.PHONY:clean
clean:
	find . -name \*.pyc -exec rm '{}' \;
	rm -rf output

.PHONY:lint
lint:
	rm -f pylint.log
	for f in `find . -name "*.py"|egrep -v 'output/'`; do pylint -i y --output-format=parseable --reports=n $$f; done 
