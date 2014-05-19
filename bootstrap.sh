#!/usr/bin/env bash

git clone https://github.com/matpow2/cuwo.git .
curl -o ./data/Server.exe http://mp2.dk/Server.exe
curl -L https://raw.githubusercontent.com/yyuu/pyenv-installer/master/bin/pyenv-installer | bash

# create run_pyenv.sh
echo "#!/usr/bin/env bash" > run_pyenv.sh
echo -e "\n\n" >> run_pyenv.sh
echo "export PYENV_ROOT=${HOME}/.pyenv" >> run_pyenv.sh
echo -e "\n\n" >> run_pyenv.sh
echo "if [ -d \"${PYENV_ROOT}\" ]; then" >> run_pyenv.sh
echo -e "\n" >> run_pyenv.sh
echo "  export PATH=\"${PYENV_ROOT}/bin:${PATH}\"" >> run_pyenv.sh
echo -e "\n" >> run_pyenv.sh
echo "  eval \"$(pyenv init -)\"" >> run_pyenv.sh
echo -e "\n" >> run_pyenv.sh
echo "fi" >> run_pyenv.sh

# create update.sh
echo "#!/usr/bin/env bash" > update.sh
echo -e "\n\n" >> update.sh
echo "cd \"$(dirname \"$0\")\""
echo -e "\n" >> update.sh
echo "sh run_pyenv.sh"
echo -e "\n" >> update.sh
echo "git pull" >> update.sh
echo -e "\n" >> update.sh
echo "python setup.py build_ext --inplace" >> update.sh

sh run_pyenv.sh

pyenv update
pyenv install 3.4.0 --skip-existing
pyenv local 3.4.0
pip install -r requirements.txt
python setup.py build_ext --inplace
